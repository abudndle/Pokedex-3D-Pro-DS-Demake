"""Synthetic checks: C92 original-data textured preview stays experimental."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c92_diagnostic_textured_preview_audit import examine

def make_archive(path, bad_uv=False, bad_texture=False, bad_map=False):
    top="diagnostic_nitrofs/"
    model="p000"
    ds=struct.pack("<4sHHII",b"DS3M",2,3,9,3)+bytes(63)
    uv=struct.pack("<4sHH",b"P3UV",1,3)+bytes(36-(1 if bad_uv else 0))
    mat=struct.pack("<4sHH4H",b"P3MT",1,1,0,3,1,9 if bad_map else 0)
    tx=struct.pack("<4sHH4H",b"P3TX",1,1,0,8,8,1)
    px=struct.pack("<4sHHH",b"P3PX",2,8,8)+bytes(128-(1 if bad_texture else 0))
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("README_EXPERIMENTAL_PRIVATE_C92.txt","PRIVATE / EXPERIMENTAL ONLY")
        z.writestr(top+"preview/"+model+".ds3m",ds)
        z.writestr(top+"preview/"+model+".p3uv",uv)
        z.writestr(top+"materials/"+model+".p3mt",mat)
        z.writestr(top+"materials/"+model+".p3tx",tx)
        z.writestr(top+"textures/"+model+"/t000.p3px",px)

class C92PreviewTests(unittest.TestCase):
    def test_valid_synthetic_preview_is_explicitly_not_release(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/"data.zip"
            make_archive(path)
            r=examine(path)
            self.assertEqual((r["diagnostic_models"],r["material_ranges"]), (1,1))
            self.assertEqual(r["sampled_triangles"],3)
            self.assertFalse(r["release_ready"])
            self.assertEqual(r["original_GPU_sampler_roles_verified"],0)
            with self.assertRaisesRegex(ValueError,"incomplete"):
                examine(path,require_full=True)
    def test_uv_mismatch_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/"bad.zip"
            make_archive(path,bad_uv=True)
            with self.assertRaisesRegex(ValueError,"P3UV"):examine(path)
    def test_texture_corruption_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/"bad.zip"
            make_archive(path,bad_texture=True)
            with self.assertRaisesRegex(ValueError,"P3PX"):examine(path)
    def test_material_reference_without_selected_image_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/"bad.zip"
            make_archive(path,bad_map=True)
            with self.assertRaisesRegex(ValueError,"material range"):examine(path)
    def test_unsafe_root_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/"bad.zip"
            make_archive(path)
            with zipfile.ZipFile(path,"a") as z:
                z.writestr("materials/p001.p3mt",b"BAD")
            with self.assertRaisesRegex(ValueError,"unsafe"):examine(path)

if __name__=="__main__":
    unittest.main()
