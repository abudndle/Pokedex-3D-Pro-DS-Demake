"""Source-free C145 packed rotation key decoder and 730-model provenance tests."""
import csv
import hashlib
import io
import json
import struct
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from c140_c5_shader_inventory import ROSTER,PART_RANGES
from c145_c5_packed_quaternions import packed_quaternions,inspect_model,audit
from test_c144_c5_timed_vectors import source_fixture


def quat_model():
    raw=bytearray(source_fixture())
    record=(0,32768,32768,32768,65535, 6,32768,32768,32768,65535)
    struct.pack_into('<10H',raw,0xd0,*record)
    return bytes(raw)


def sample_archives(root):
    raw=quat_model()
    digest=hashlib.sha256(raw).hexdigest()
    rows=[];prior={};parts=[]
    for index,(low,high) in enumerate(PART_RANGES):
        archive=root/f'c56-{index}.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for model in range(low,high+1):
                if model not in ROSTER:continue
                name=f'p{model:03d}'
                z.writestr(f'decoded_c5/{name}.c5',raw)
                rows.append({'model':name,'sha256':digest,'decoded_bytes':str(len(raw))})
                prior[name]={'source_sha256':digest,'group_count':1}
        parts.append(archive)
    stream=io.StringIO()
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    reference=root/'decoder.zip'
    with zipfile.ZipFile(reference,'w') as z:z.writestr('C56_validation.csv',stream.getvalue())
    report=root/'c144.json'
    report.write_text(json.dumps({'c56_models_verified':730,
                                 'c143_ordered_groups_verified':730,
                                 'models':prior}))
    return parts,reference,report

class C145Tests(unittest.TestCase):
    def test_source_quaternion_packed_records(self):
        b=quat_model()
        decoded=inspect_model(b,detailed=True)
        self.assertEqual(decoded['source_three_channel_groups'],1)
        self.assertEqual(decoded['source_quaternion_candidate_keys'],2)
        self.assertEqual(decoded['maximum_time_tag'],6)
        self.assertEqual(decoded['zero_alignment_padding_bytes'],0)
        self.assertEqual(decoded['max_squared_norm_error'],0)
        self.assertFalse(decoded['original_bone_attachments_verified'])
        keys=decoded['packed_groups'][0]['keys']
        self.assertEqual([k['time_tag'] for k in keys],[0,6])
        self.assertEqual(keys[0]['normalized_components_source_order'],[0.,0.,0.,1.])

    def test_optional_zero_padding_and_bad_alignment(self):
        q=struct.pack('<15H',0,32768,32768,32768,65535,
                                2,32768,32768,32768,65535,
                                6,32768,32768,32768,65535)
        self.assertEqual(packed_quaternions(q+b'\0\0',0,32)['zero_alignment_padding_bytes'],2)
        with self.assertRaisesRegex(ValueError,'padding'):
            packed_quaternions(q+b'\0\1',0,32)
        with self.assertRaisesRegex(ValueError,'alignment'):
            packed_quaternions(q+b'\0',0,31)

    def test_reject_nonunit_and_unordered_original_records(self):
        raw=bytearray(quat_model())
        struct.pack_into('<H',raw,0xd0+2,32768)
        struct.pack_into('<H',raw,0xd0+4,32768)
        struct.pack_into('<H',raw,0xd0+6,32768)
        struct.pack_into('<H',raw,0xd0+8,32768)
        with self.assertRaisesRegex(ValueError,'not normalized'):
            inspect_model(bytes(raw))
        raw=bytearray(quat_model())
        struct.pack_into('<H',raw,0xd0+10,0)
        with self.assertRaisesRegex(ValueError,'unordered'):
            inspect_model(bytes(raw))

    def test_all_730_synthetic_models_bound_to_original_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            parts,reference,report=sample_archives(root)
            result=audit(parts,reference,report)
            self.assertEqual(result['c56_source_models_verified'],730)
            self.assertEqual(result['c144_channel_groups_verified'],730)
            self.assertEqual(result['decoded_packed_rotation_like_keyframes'],1460)
            self.assertEqual(result['maximum_normalization_squared_error'],0)
            self.assertFalse(result['native_animation_activated'])
            with self.assertRaisesRegex(ValueError,'displaced'):
                audit(parts[::-1],reference,report)
            data=json.loads(report.read_text())
            data['models']['p010']['source_sha256']='0'*64
            report.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'source mismatch'):
                audit(parts,reference,report)

if __name__=='__main__':unittest.main()