"""Synthetic original C5 owner/rotation-count/duration control validations."""
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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from c146_c5_owner_control_fields import inspect_model,audit
from c140_c5_shader_inventory import ROSTER,PART_RANGES
from test_c145_c5_packed_quaternions import quat_model


def source():
    b=bytearray(quat_model())
    for i in range(3):struct.pack_into('<I',b,0x80+i*16+8,(2<<16)|6)
    return bytes(b)


def fixture(root):
    b=source();sha=hashlib.sha256(b).hexdigest();parts=[];rows=[];base={}
    for index,(lo,hi) in enumerate(PART_RANGES):
        path=root/f'part{index}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for idx in range(lo,hi+1):
                if idx not in ROSTER:continue
                label=f'p{idx:03d}'
                z.writestr(f'decoded_c5/{label}.c5',b)
                rows.append({'model':label,'sha256':sha,'decoded_bytes':str(len(b))})
                base[label]={'source_sha256':sha,'source_group_count':1,'original_quaternion_candidate_keys':2}
        parts.append(path)
    table=io.StringIO();writer=csv.DictWriter(table,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    bundle=root/'decoder.zip'
    with zipfile.ZipFile(bundle,'w') as z:z.writestr('C56_validation.csv',table.getvalue())
    prior=root/'c145.json';prior.write_text(json.dumps({'c56_source_models_verified':730,
        'c144_channel_groups_verified':730,'decoded_packed_rotation_like_keyframes':1460,'models':base}))
    return parts,bundle,prior

class C146Tests(unittest.TestCase):
    def test_original_count_duration_and_owner_control(self):
        info=inspect_model(source(),detailed=True)
        self.assertEqual(info['candidate_groups'],1)
        self.assertEqual(info['packed_quaternion_keyframes'],2)
        self.assertEqual(info['unique_owner_tokens'],1)
        row=info['source_group_control_records'][0]
        self.assertEqual(row['high16_source_q_key_count'],2)
        self.assertEqual(row['low16_source_end_time_tag'],6)
        self.assertFalse(info['source_owner_tokens_are_bone_ids_verified'])

    def test_wrong_source_duration_or_quat_count_fails(self):
        for control in ((2<<16)|7,(3<<16)|6):
            b=bytearray(source())
            for j in range(3):struct.pack_into('<I',b,0x80+j*16+8,control)
            with self.assertRaisesRegex(ValueError,'control word count/time tag'):
                inspect_model(bytes(b))

    def test_reject_zero_owner_and_mismatched_reference(self):
        b=bytearray(source())
        for j in range(3):struct.pack_into('<I',b,0x80+j*16+4,0)
        with self.assertRaisesRegex(ValueError,'owner token'):
            inspect_model(bytes(b))

    def test_full_730_sha_bound_source_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parts,bundle,baseline=fixture(root)
            report=audit(parts,bundle,baseline)
            self.assertEqual(report['c56_models_verified'],730)
            self.assertEqual(report['control_high16_equals_packed_key_count'],730)
            self.assertEqual(report['control_low16_equals_common_end_time_tag'],730)
            self.assertEqual(report['models_with_unique_owner_tokens'],730)
            self.assertFalse(report['owner_tokens_proven_skeleton_bone_ids'])
            with self.assertRaisesRegex(ValueError,'displaced'):
                audit(parts[::-1],bundle,baseline)
            data=json.loads(baseline.read_text())
            data['models']['p000']['source_sha256']='0'*64
            baseline.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'source digest mismatch'):
                audit(parts,bundle,baseline)

if __name__=='__main__':unittest.main()