"""Synthetic-only regression for C143 repeating source-record channel candidates."""
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c140_c5_shader_inventory import ROSTER, PART_RANGES
from c142_c5_track_index import parse_source_tracks
from c143_c5_channel_groups import CHANNEL_CODES, group_candidates, audit


def source_fixture(*, owner_mismatch=False, low16_mismatch=False, bad_code=False):
    b=bytearray(0x180)
    b[:2]=b'\xc5\x78'
    struct.pack_into('<H', b, 0x1a, 4)
    for offset, value in [(0x48,0x80),(0x4c,0xc0),(0x64,0x160),(0x68,0xd0)]:
        struct.pack_into('<I',b,offset,value)
    for i, ptr in enumerate((0xd0,0xf0,0x110,0x130)):
        code=CHANNEL_CODES[i] if i<3 else 0x0402044d
        owner=0x12000001 + (i==2 and owner_mismatch)
        low=0x73 + (i==2 and low16_mismatch)
        if i==1 and bad_code:code=0x0402044d
        struct.pack_into('<4I',b,0x80+16*i,ptr,owner,2<<16|low,code)
    for i in range(0xd0,0x160):b[i]=(i*19)&255
    return bytes(b)


def archive_fixture(root):
    model=source_fixture()
    digest=hashlib.sha256(model).hexdigest()
    parts=[]
    csv_rows=[]
    baseline={}
    summary=parse_source_tracks(model,include_records=False)
    for index,(lo,hi) in enumerate(PART_RANGES):
        path=root/f'part{index}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n in range(lo,hi+1):
                if n not in ROSTER:continue
                label=f'p{n:03d}'
                z.writestr(f'decoded_c5/{label}.c5',model)
                csv_rows.append({'model':label,'sha256':digest,'decoded_bytes':str(len(model)),
                                 'status':'strict_valid','0x26_descriptor_flags':'0',
                                 'primary_descriptor_count':'1','error':''})
                baseline[label]={'source_sha256':digest,'source_track_records':4,
                                 'track_payload_aggregate_sha256':summary['track_payload_aggregate_sha256'],
                                 'track_payload_bytes':summary['track_payload_bytes']}
        parts.append(path)
    tools=root/'decoder.zip'
    with zipfile.ZipFile(tools,'w') as z:
        output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=list(csv_rows[0]))
        writer.writeheader();writer.writerows(csv_rows)
        z.writestr('C56_validation.csv',output.getvalue())
    prior=root/'prior.json'
    prior.write_text(json.dumps({'c56_models_verified':730,
        'c142_pointer_indexed_source_records':2920,'models':baseline}))
    return parts,tools,prior


class ChannelCandidatesTests(unittest.TestCase):
    def test_exact_triplet_and_opaque_remainder(self):
        row=group_candidates(source_fixture(),detailed=True)
        self.assertEqual(row['three_channel_candidates'],1)
        self.assertEqual(row['matched_source_records'],3)
        self.assertEqual(row['unclassified_source_records'],1)
        self.assertEqual(row['unclassified_code_counts'],{'0x0402044d':1})
        self.assertEqual(len(row['candidate_groups']),1)
        self.assertFalse(row['channel_group_semantics_verified'])
        self.assertFalse(row['material_face_links_verified'])

    def test_reject_ambiguous_owner_low_word_or_wrong_code(self):
        for kwargs in ({'owner_mismatch':True},{'low16_mismatch':True},{'bad_code':True}):
            result=group_candidates(source_fixture(**kwargs))
            self.assertEqual(result['three_channel_candidates'],0)
            self.assertEqual(result['unclassified_source_records'],4)

    def test_reject_corrupt_source_record_bounds(self):
        bad=bytearray(source_fixture())
        struct.pack_into('<I',bad,0x80,0xfffffff0)
        with self.assertRaisesRegex(ValueError,'pointer'):
            group_candidates(bytes(bad))
        with self.assertRaises(ValueError):group_candidates(b'not a model')

    def test_full_synthetic_730_source_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            parts,decoder,prior=archive_fixture(root)
            result=audit(parts,decoder,prior)
            self.assertEqual(result['c56_models_verified'],730)
            self.assertEqual(result['ordered_three_channel_candidates'],730)
            self.assertEqual(result['matched_source_records'],2190)
            self.assertEqual(result['unclassified_source_records'],730)
            self.assertEqual(result['verified_face_material_links'],0)
            self.assertNotIn('candidate_groups',result['models']['p000'])
            # Reversed parts are not valid original C56 provenance.
            with self.assertRaisesRegex(ValueError,'displaced'):
                audit(parts[::-1],decoder,prior)
            # Tampering with prior verified track data is also rejected.
            payload=json.loads(prior.read_text())
            payload['models']['p025']['track_payload_aggregate_sha256']='f'*64
            prior.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,'C142 track checksum'):
                audit(parts,decoder,prior)


if __name__=='__main__':unittest.main()