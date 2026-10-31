"""Synthetic C94 UV/source face-topology regression tests; no game assets."""
import pathlib
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c94_original_obj_uv_alignment import read_topology,validate_pair,audit

BASE=b'o p000_mesh_0\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
UV=b'vt 0.5 0.5\nvt 0 0\nvt 1 -1\n'+BASE.replace(b'f 1 2 3',b'f 1/1 2/2 3/3')

class OriginalSourceUvs(unittest.TestCase):
    def test_exact_face_and_xyz_order_pass(self):
        r=validate_pair(BASE,UV)
        self.assertEqual(r["faces"],1)
        self.assertFalse(r["original_3ds_sampler_channels_verified"])
    def test_swapped_original_source_triangle_rejected(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            validate_pair(BASE,UV.replace(b'1/1 2/2 3/3',b'2/2 1/1 3/3'))
    def test_moved_original_source_vertex_rejected(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            validate_pair(BASE,UV.replace(b'v 1 0 0',b'v 1 1 0'))
    def test_missing_uv_rejected(self):
        with self.assertRaisesRegex(ValueError,"UV missing"):
            validate_pair(BASE,BASE)
    def test_invalid_fixed_uv_range_rejected(self):
        with self.assertRaisesRegex(ValueError,"signed DS"):
            validate_pair(BASE,UV.replace(b'vt 0.5 0.5',b'vt 9.0 0.5'))
    def test_bad_vertex_reference_rejected(self):
        with self.assertRaisesRegex(ValueError,"vertex index"):
            validate_pair(BASE,UV.replace(b'1/1 2/2 3/3',b'1/1 2/2 99/3'))
    def test_zip_inventory_respects_unchanged_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            a=root/"c7.zip";b=root/"c62.zip"
            with zipfile.ZipFile(a,"w") as f:
                f.writestr("models/p000.obj",BASE)
            with zipfile.ZipFile(b,"w") as f:
                f.writestr("C62/p000.obj",UV)
            r=audit(a,b,["p000"])
            self.assertEqual(r["full_obj_pairs_verified"],1)
            self.assertEqual(r["source_triangle_count"],1)
            self.assertEqual(r["source_c62_uv_models"],1)
            self.assertEqual(r["failures"],{})
            with zipfile.ZipFile(b,"w") as f:
                f.writestr("C62/p000.obj",UV.replace(b'1/1 2/2 3/3',b'3/3 2/2 1/1'))
            self.assertIn("p000",audit(a,b,["p000"])["failures"])

if __name__=="__main__":unittest.main()
