"""Synthetic C79 private texture manifest tests; no Nintendo data used."""
import csv
import hashlib
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from c79_private_texture_manifest_builder import p3tx_bytes, scan


def make_fixture(root, bad_hash=False, wrong_count=False):
    px = struct.pack("<4sHHH", b"P3PX", 2, 8, 8) + struct.pack("<64H", *([0x8123] * 64))
    with zipfile.ZipFile(root / "tex.zip", "w") as archive:
        archive.writestr("textures/p000/t000.p3px", px)
    rows = [{"model_id":"p000", "index":"0", "ds_width":"8",
             "ds_height":"8", "output_path":"textures/p000/t000.p3px",
             "p3px_sha256":"0"*64 if bad_hash else hashlib.sha256(px).hexdigest()}]
    with (root / "texture.csv").open("w", newline="") as fp:
        writer=csv.DictWriter(fp, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    def catalog(model, count):
        name=b"synthetic_test"
        record=struct.pack("<HHHII32sH",0,8,8,99,123,b"X"*32,len(name))+name if count else b""
        return struct.pack("<4s4HII", b"P3TM",1,model,count,0,len(record),zlib.crc32(record))+record
    with zipfile.ZipFile(root/"catalog.zip","w") as archive:
        archive.writestr("catalogs/p000.p3tm",catalog(0,0 if wrong_count else 1))
        archive.writestr("catalogs/p001.p3tm",catalog(1,0))
    return root/"texture.csv",root/"tex.zip",root/"catalog.zip"


class TestC79(unittest.TestCase):
    def test_manifest_bytes(self):
        self.assertEqual(p3tx_bytes([(0,8,8)]), struct.pack("<4sHH4H",b"P3TX",1,1,0,8,8,1))
    def test_duplicate_index_rejected(self):
        with self.assertRaises(ValueError):
            p3tx_bytes([(0,8,8),(0,8,8)])
    def test_invalid_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            p3tx_bytes([(0,7,8)])
    def test_fixture_builds_one_manifest_and_skips_empty_model(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            a,b,c=make_fixture(root)
            rows,summary=scan(a,b,c,root/"output.zip")
            self.assertEqual(summary["models"],2)
            self.assertEqual(summary["model_manifest_count"],1)
            self.assertEqual(summary["verified_p3px"],1)
            self.assertFalse(rows[1]["manifest_generated"])
            with zipfile.ZipFile(root/"output.zip") as archive:
                self.assertEqual(archive.read("materials/p000.p3tx"),p3tx_bytes([(0,8,8)]))
                self.assertNotIn("materials/p001.p3tx",archive.namelist())
                self.assertFalse(any(".p3px" in name for name in archive.namelist()))
    def test_bad_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):scan(*make_fixture(pathlib.Path(d),bad_hash=True))
    def test_catalog_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):scan(*make_fixture(pathlib.Path(d),wrong_count=True))


if __name__=="__main__":
    unittest.main()
