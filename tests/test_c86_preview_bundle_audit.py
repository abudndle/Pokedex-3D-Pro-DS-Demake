"""C86 public-safe synthetic DS3M/P3UV pairing regression tests."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from c86_preview_bundle_audit import audit,inspect_ds3m,inspect_uv

def fixture(uv_count=1):
    ds=struct.pack('<4sHHII',b'DS3M',2,1,3,1)
    ds+=struct.pack('<9h',0,0,0,4096,0,0,0,4096,0)+bytes((192,224,232))
    uv=struct.pack('<4sHH',b'P3UV',1,uv_count)+bytes(12*uv_count)
    return ds,uv

class TestC86Pairing(unittest.TestCase):
    def test_valid_pair_and_missing_roster(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/'test.zip'
            ds,uv=fixture()
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('preview/p000.ds3m',ds)
                z.writestr('uv_candidates/p000.ds3m',ds)
                z.writestr('uv_candidates/p000.p3uv',uv)
            result=audit(path)
            self.assertEqual(result['fallback_previews'],1)
            self.assertEqual(result['paired_source_uv_candidates'],1)
            self.assertFalse(result['visual_accuracy_verified'])
            with self.assertRaisesRegex(ValueError,'incomplete'):
                audit(path,require_full=True)
    def test_orphan_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/'test.zip'
            ds,_=fixture()
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('uv_candidates/p000.ds3m',ds)
            with self.assertRaisesRegex(ValueError,'matching'):
                audit(path)
    def test_triangle_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/'test.zip'
            ds,_=fixture()
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('preview/p000.ds3m',ds)
                z.writestr('uv_candidates/p000.ds3m',ds)
                z.writestr('uv_candidates/p000.p3uv',fixture(2)[1])
            with self.assertRaisesRegex(ValueError,'triangle-count'):
                audit(path)
    def test_truncation_and_overflow_rejected(self):
        ds,uv=fixture()
        with self.assertRaisesRegex(ValueError,'size'):
            inspect_ds3m(ds[:-1])
        with self.assertRaisesRegex(ValueError,'size'):
            inspect_uv(uv[:-2])
        with self.assertRaisesRegex(ValueError,'overflow'):
            inspect_ds3m(ds[:16]+struct.pack('<h',32767)+ds[18:])
    def test_gap_model_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/'test.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('preview/p721.ds3m',fixture()[0])
            with self.assertRaisesRegex(ValueError,'unexpected'):
                audit(path)
if __name__=='__main__':unittest.main()
