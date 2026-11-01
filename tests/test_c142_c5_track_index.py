"""C142: synthetic source-only track pointer/provenance regression."""
import csv
import hashlib
import io
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from c142_c5_track_index import parse_source_tracks, audit
from c140_c5_shader_inventory import ROSTER, PART_RANGES


def source_c5(*, bad_count=False, reversed_pointers=False, unaligned=False):
    b = bytearray(0x140)
    b[:2] = b"\xc5\x78"
    struct.pack_into('<H', b, 0x1a, 3 if bad_count else 2)
    for offset, value in ((0x48,0x80),(0x4c,0xa0),(0x64,0xf0),(0x68,0xb0)):
        struct.pack_into('<I',b,offset,value)
    pointers = (0xd0,0xb0) if reversed_pointers else (0xb0,0xd0)
    if unaligned: pointers = (0xb1,0xd0)
    for i, p in enumerate(pointers):
        struct.pack_into('<4I',b,0x80+16*i,p,0x1234+i,0xabc,0xfeed)
    for i in range(0xb0,0xf0): b[i]=(i * 17) & 0xff
    b[0xf0:0xf0+len(b'kawa;;;CF_COLORMAP\0')]=b'kawa;;;CF_COLORMAP\0'
    return bytes(b)


def zip_fixture(root):
    parts=[]; models={}; rows=[]; mesh_models={}
    data = source_c5()
    digest = hashlib.sha256(data).hexdigest()
    for idx,(lo,hi) in enumerate(PART_RANGES):
        path=root/f'part{idx+1}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for model in range(lo,hi+1):
                if model not in ROSTER: continue
                label=f'p{model:03d}'
                z.writestr(f'decoded_c5/{label}.c5',data)
                rows.append({'model':label,'sha256':digest,'decoded_bytes':str(len(data))})
                models[label]={'source_c5_sha256':digest,'shader_declarations':[{'program':'kawa','flags':['CF_COLORMAP']}]}
                mesh_models[label]={'source_sha256':digest,'source_mesh_groups':1,'source_triangle_count':3,'preview_triangles':1}
        parts.append(path)
    bundle=root/'C56_validation.zip'
    with zipfile.ZipFile(bundle,'w') as z:
        stream=io.StringIO()
        writer=csv.DictWriter(stream,fieldnames=['model','sha256','decoded_bytes'])
        writer.writeheader();writer.writerows(rows)
        z.writestr('C56_validation.csv',stream.getvalue())
    c140=root/'c140.json';c141=root/'c141.json'
    c140.write_text(json.dumps({'models_verified':730,'models':models}))
    c141.write_text(json.dumps({'original_c56_models_verified':730,'models':mesh_models}))
    native=root/'private_nitrofs.zip'
    header=struct.pack('<4sHHII',b'DS3M',2,1,0,3)+bytes(21)
    with zipfile.ZipFile(native,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for model in sorted(ROSTER): z.writestr(f'preview/p{model:03d}.ds3m',header)
    return parts,bundle,c140,c141,native


class C142Tests(unittest.TestCase):
    def test_original_source_track_spans_and_controls_remain_opaque(self):
        raw=source_c5()
        found=parse_source_tracks(raw)
        self.assertEqual(found['source_track_records'],2)
        self.assertEqual(found['track_payload_bytes'],64)
        self.assertEqual(found['record_span_histogram'],{'32':2})
        self.assertFalse(found['source_track_records_are_material_bindings'])
        self.assertEqual(found['records'][0]['source_payload_start'],0xb0)
        self.assertEqual(found['records'][1]['source_payload_end'],0xf0)
        self.assertEqual(found['records'][0]['control_words_opaque'],['0x00001234','0x00000abc','0x0000feed'])
        self.assertEqual(found['records'][0]['payload_sha256'],hashlib.sha256(raw[0xb0:0xd0]).hexdigest())

    def test_reject_unordered_unaligned_and_inconsistent_source_headers(self):
        for obj in (source_c5(bad_count=True),source_c5(reversed_pointers=True),source_c5(unaligned=True)):
            with self.subTest(obj=obj[0x1a:0x1c]+obj[0x80:0x84]):
                with self.assertRaisesRegex(ValueError, 'mismatch|pointer'):
                    parse_source_tracks(obj)
        broken=bytearray(source_c5())
        struct.pack_into('<I',broken,0x68,0x200)
        with self.assertRaisesRegex(ValueError,'boundaries'):
            parse_source_tracks(bytes(broken))

    def test_complete_730_synthetic_hash_cross_stage_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            parts,bundle,c140,c141,nitro=zip_fixture(pathlib.Path(temp))
            result=audit(parts,bundle,c140,c141,nitro)
            self.assertEqual(result['c56_models_verified'],730)
            self.assertEqual(result['c140_shader_declarations_cross_verified'],730)
            self.assertEqual(result['c141_source_mesh_groups_cross_verified'],730)
            self.assertEqual(result['c142_pointer_indexed_source_records'],1460)
            self.assertEqual(result['c142_source_track_payload_bytes'],730*64)
            self.assertEqual(result['private_preview_source_count_verified'],730)
            self.assertEqual(result['certified_original_textured_models'],0)
            fast=audit(parts,bundle,c140,c141,nitro,include_records=False)
            self.assertEqual(fast['c142_pointer_indexed_source_records'],1460)
            self.assertFalse(fast['source_track_record_details_included'])
            self.assertEqual(fast['models']['p000']['records'],[])
            self.assertEqual(fast['models']['p000']['track_payload_aggregate_sha256'],result['models']['p000']['track_payload_aggregate_sha256'])

    def test_reject_stale_c140_c141_cross_stage_report_and_duplicate_native(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            parts,bundle,c140,c141,nitro=zip_fixture(root)
            report=json.loads(c141.read_text())
            report['models']['p000']['source_triangle_count']=999
            c141.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'does not match verified C141 metadata'):
                audit(parts,bundle,c140,c141,nitro)
            report['models']['p000']['source_triangle_count']=3
            c141.write_text(json.dumps(report))
            with zipfile.ZipFile(nitro,'a') as z:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore',UserWarning)
                    z.writestr('preview/p000.ds3m',b'corrupt')
            with self.assertRaisesRegex(ValueError,'ambiguous private preview ZIP'):
                audit(parts,bundle,c140,c141,nitro)


if __name__=='__main__': unittest.main()