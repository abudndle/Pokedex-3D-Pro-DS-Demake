import sys
import io
import zipfile
import tempfile
import struct
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c170_geometry_layout_evidence import inspect, audit

def fixture(io=200):
    raw=bytearray(224)
    raw[:2]=bytes((0xc5,0x78))
    struct.pack_into("<H",raw,0x10,1)
    struct.pack_into("<2H",raw,0x14,1,1)
    struct.pack_into("<H",raw,0x18,1)
    struct.pack_into("<3I",raw,0x3c,120,140,152)
    struct.pack_into("<I",raw,0x50,192)
    struct.pack_into("<5I",raw,120,196,0,4,0,0)
    struct.pack_into("<3I",raw,140,io,0,(2<<16)|6)
    struct.pack_into("<8H",raw,152,0,0,0,0,2,0,0,0x0c02)
    return bytes(raw)
class C170Tests(unittest.TestCase):
    def test_reject_unexpected_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(Path(tmp)/"Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip", "w") as z:
                z.writestr("README.txt", b"unexpected")
            with self.assertRaisesRegex(ValueError, "unexpected source C5"):
                audit(Path(tmp))

    def test_reject_duplicate_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(Path(tmp)/"Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip", "w") as z:
                z.writestr("decoded_c5/p000.c5", fixture())
                z.writestr("decoded_c5/p000.c5", fixture())
            with self.assertRaisesRegex(ValueError, "duplicate ZIP member"):
                audit(Path(tmp))

    def test_descriptor_relationship(self):
        self.assertEqual(inspect(fixture()),[(196,200,4,6,2)])
    def test_invalid_payload_offset(self):
        with self.assertRaises(ValueError):inspect(fixture(225))
    def test_invalid_magic(self):
        with self.assertRaises(ValueError):inspect(bytes(224))
if __name__=="__main__":unittest.main()
