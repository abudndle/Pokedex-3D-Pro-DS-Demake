"""Synthetic C144 full source audit and strict float/time validation regression."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tools'))
from c144_c5_timed_vectors import read_timed_vec3,inspect_model,audit
from c140_c5_shader_inventory import ROSTER,PART_RANGES
from c143_c5_channel_groups import group_candidates


def source_fixture(*,bad_time=False,nonfinite=False):
    b=bytearray(0x200)
    b[:2]=b'\xc5\x78'
    struct.pack_into('<H',b,0x1a,4)
    for at,val in ((0x48,0x80),(0x4c,0xc0),(0x64,0x190),(0x68,0xd0)):
        struct.pack_into('<I',b,at,val)
    for i,offset in enumerate((0xd0,0xe4,0x104,0x144)):
        struct.pack_into('<4I',b,0x80+i*16,offset,0xabcd if i<3 else 2,
                         0x20011 if i<3 else 0, (0x40071,0x30053,0x30054,0x0402044d)[i])
    for k in range(0xd0,0x190):b[k]=(k*17)&0xff
    struct.pack_into('<8f',b,0xe4,0.,1.,2.,3., 6.,4.,5.,6.)
    vals=[(0.,0.1,0.2,0.3),(2.,0.2,0.4,0.6),(4.,0.3,0.6,0.9),(6.,0.5,1.,1.5)]
    if bad_time: vals[2]=(2.,0.3,0.6,0.9)
    if nonfinite: vals[1]=(2.,math.nan,0.4,0.6)
    for i,row in enumerate(vals):struct.pack_into('<4f',b,0x104+i*16,*row)
    return bytes(b)


def archive_fixture(root):
    raw=source_fixture()
    digest=hashlib.sha256(raw).hexdigest()
    item=group_candidates(raw)
    parts=[];csv_rows=[];prior={}
    for index,(lo,hi) in enumerate(PART_RANGES):
        path=root/f'part{index}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for model in range(lo,hi+1):
                if model not in ROSTER:continue
                label=f'p{model:03d}'
                z.writestr(f'decoded_c5/{label}.c5',raw)
                csv_rows.append({'model':label,'sha256':digest,'decoded_bytes':str(len(raw))})
                prior[label]={
                    'source_sha256':digest,
                    'source_track_records':item['source_track_records'],
                    'three_channel_candidates':item['three_channel_candidates'],
                    'source_track_payload_aggregate_sha256':item['source_track_payload_aggregate_sha256']}
        parts.append(path)
    bundle=root/'decoder.zip'
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    with zipfile.ZipFile(bundle,'w') as z:z.writestr('C56_validation.csv',output.getvalue())
    summary=root/'c143.json'
    summary.write_text(json.dumps({'c56_models_verified':730,'ordered_three_channel_candidates':730,'models':prior}))
    return parts,bundle,summary

class C144Tests(unittest.TestCase):
    def test_two_original_timed_vec3_streams(self):
        raw=source_fixture()
        info=inspect_model(raw,detailed=True)
        self.assertEqual(info['candidate_group_count'],1)
        self.assertEqual((info['first_vector_keyframes'],info['second_vector_keyframes']),(2,4))
        self.assertEqual(info['maximum_time_tag'],6)
        self.assertEqual(info['paired_final_timestamps_match'],1)
        self.assertEqual(info['identical_full_timestamps'],0)
        self.assertFalse(info['bone_attachment_verified'])
        channel=info['groups'][0]['timed_vector_channels'][1]
        self.assertEqual([r['time_tag'] for r in channel['values']],[0,2,4,6])
        self.assertEqual(info['opaque_first_channel_length_mod10'],{'0':1})

    def test_fail_closed_on_nan_unordered_or_invalid_time(self):
        for bad in (source_fixture(bad_time=True),source_fixture(nonfinite=True)):
            with self.assertRaisesRegex(ValueError,'unordered|nonfinite'):
                inspect_model(bad)
        with self.assertRaisesRegex(ValueError,'invalid 16-byte'):
            read_timed_vec3(source_fixture(),0xe4,0x103)
        raw=bytearray(source_fixture())
        struct.pack_into('<f',raw,0xe4,1.0)
        with self.assertRaisesRegex(ValueError,'time zero'):
            inspect_model(bytes(raw))

    def test_730_model_synthetic_sha_bound_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            parts,bundle,report=archive_fixture(root)
            result=audit(parts,bundle,report)
            self.assertEqual(result['c56_models_verified'],730)
            self.assertEqual(result['c143_ordered_groups_verified'],730)
            self.assertEqual(result['decoded_time_float3_streams'],1460)
            self.assertEqual(result['total_time_float3_keyframes'],4380)
            self.assertEqual(result['maximum_source_time_tag'],6)
            self.assertFalse(result['precise_bone_transform_roles_verified'])
            self.assertFalse(result['source_face_to_material_mapping_verified'])

    def test_displaced_source_or_prior_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            parts,bundle,report=archive_fixture(root)
            with self.assertRaisesRegex(ValueError,'out-of-order'):
                audit(parts[::-1],bundle,report)
            data=json.loads(report.read_text())
            data['models']['p002']['source_track_payload_aggregate_sha256']='f'*64
            report.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'C143 track group identity'):
                audit(parts,bundle,report)

if __name__=='__main__':unittest.main()