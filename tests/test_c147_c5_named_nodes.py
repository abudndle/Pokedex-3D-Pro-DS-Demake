"""No Nintendo data: C147 original string-offset owner association regressions."""
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
from c147_c5_named_nodes import resolve_string,inspect_model,audit
from c140_c5_shader_inventory import ROSTER,PART_RANGES
from test_c146_c5_owner_control_fields import source


def named_source(*,suffix=False):
    raw=bytearray(source())
    if suffix:
        raw[0x190:0x190+9]=b'SomeRoot\0'
        for i in range(3):struct.pack_into('<I',raw,0x80+16*i+4,(4<<16)|0xabcd)
    else:
        raw[0x190:0x190+9]=b'BoneRoot\0'
    return bytes(raw)


def archive_fixture(folder):
    raw=named_source();digest=hashlib.sha256(raw).hexdigest()
    parts=[];csvrows=[];baseline={}
    for index,(lo,hi) in enumerate(PART_RANGES):
        archive=folder/f'part{index}.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for model in range(lo,hi+1):
                if model not in ROSTER:continue
                name=f'p{model:03d}'
                z.writestr(f'decoded_c5/{name}.c5',raw)
                csvrows.append({'model':name,'sha256':digest,'decoded_bytes':str(len(raw))})
                baseline[name]={'source_sha256':digest,'source_groups':1}
        parts.append(archive)
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=list(csvrows[0]));writer.writeheader();writer.writerows(csvrows)
    reference=folder/'decoder.zip'
    with zipfile.ZipFile(reference,'w') as z:z.writestr('C56_validation.csv',out.getvalue())
    summary=folder/'c146.json';summary.write_text(json.dumps({
        'c56_models_verified':730,'source_c5_groups_verified':730,'models':baseline}))
    return parts,reference,summary

class C147Tests(unittest.TestCase):
    def test_exact_node_name_source_owner_mapping(self):
        result=inspect_model(named_source(),detailed=True)
        self.assertEqual(result['source_named_channel_groups'],1)
        self.assertEqual(result['source_interned_string_suffix_references'],0)
        self.assertEqual(result['original_source_named_node_tracks'][0]['original_node_name'],'BoneRoot')
        self.assertFalse(result['original_bone_hierarchy_proven'])

    def test_suffix_interning_is_not_incorrectly_rebased(self):
        raw=named_source(suffix=True)
        self.assertEqual(resolve_string(raw,0x190,4),('Root',True))
        result=inspect_model(raw,detailed=True)
        self.assertEqual(result['source_interned_string_suffix_references'],1)
        self.assertEqual(result['original_source_named_node_tracks'][0]['original_node_name'],'Root')

    def test_malformed_or_dangerous_original_name_pointers_rejected(self):
        raw=bytearray(named_source())
        for i in range(3):struct.pack_into('<I',raw,0x80+16*i+4,(0xffff<<16)|0xabcd)
        with self.assertRaisesRegex(ValueError,'pointer outside'):
            inspect_model(bytes(raw))
        raw=bytearray(named_source())
        raw[0x190]=0xff
        with self.assertRaisesRegex(ValueError,'nonprintable'):
            inspect_model(bytes(raw))
        raw=bytearray(named_source())
        raw[0x190:]=b'Z'*(len(raw)-0x190)
        with self.assertRaisesRegex(ValueError,'unterminated'):
            inspect_model(bytes(raw))

    def test_all_730_synthetic_source_models_and_sha_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);parts,reference,summary=archive_fixture(root)
            output=audit(parts,reference,summary)
            self.assertEqual(output['original_C56_models_verified'],730)
            self.assertEqual(output['source_C5_named_node_tracks_verified'],730)
            self.assertEqual(output['models_with_unique_source_track_node_names'],730)
            self.assertTrue(output['bone_name_association_source_verified'])
            self.assertFalse(output['bone_parent_hierarchy_verified'])
            with self.assertRaisesRegex(ValueError,'displaced'):
                audit(parts[::-1],reference,summary)
            d=json.loads(summary.read_text())
            d['models']['p000']['source_sha256']='0'*64
            summary.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'digest mismatch'):
                audit(parts,reference,summary)

if __name__=='__main__':unittest.main()