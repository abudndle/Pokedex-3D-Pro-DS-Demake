import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c169_descriptor_payload_evidence import inspect

def fixture(payload):
    raw=bytearray(224)
    raw[:2]=bytes((0xc5,0x78))
    struct.pack_into("<H",raw,0x10,1)
    struct.pack_into("<2H",raw,0x14,1,1)
    struct.pack_into("<H",raw,0x18,1)
    struct.pack_into("<3I",raw,0x3c,120,140,152)
    struct.pack_into("<I",raw,0x50,192)
    struct.pack_into("<5I",raw,120,0,0,4,0,0)
    struct.pack_into("<3I",raw,140,200,0,6)
    struct.pack_into("<8H",raw,152,0,0,0,0,2,0,0,0x0c02)
    struct.pack_into("<6H",raw,200,*payload)
    return bytes(raw)
class C169Tests(unittest.TestCase):
    def test_valid_u16_not_proven(self):
        r=inspect(fixture([0,1,2,1,2,3]))
        self.assertEqual(r["u16_index_incompatible"],0)
    def test_incompatible_u16(self):
        self.assertEqual(inspect(fixture([0,1,2,65535,2,3]))["u16_index_incompatible"],1)
    def test_invalid_magic(self):
        with self.assertRaises(ValueError):inspect(bytes(224))
if __name__=="__main__":unittest.main()
