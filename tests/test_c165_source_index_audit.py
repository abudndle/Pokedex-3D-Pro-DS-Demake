import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c165_source_index_audit import inspect_source

class C165Tests(unittest.TestCase):
    def test_reject_short_header(self):
        with self.assertRaises(ValueError):inspect_source(b"")
    def test_reject_fake_magic(self):
        with self.assertRaises(ValueError):inspect_source(b"not a C5"+bytes(200))
    def test_no_inferred_geometry_evidence(self):
        # Valid minimal C5 draw table with one mesh and one primary draw.
        raw=bytearray(212)
        raw[:2]=b"\\xc5x".decode("unicode_escape").encode("latin1")
        struct.pack_into("<H",raw,0x10,1)
        struct.pack_into("<2H",raw,0x14,1,1)
        struct.pack_into("<H",raw,0x18,1)
        struct.pack_into("<3I",raw,0x3c,120,140,152)
        struct.pack_into("<I",raw,0x50,192)
        struct.pack_into("<I",raw,148,6)
        struct.pack_into("<8H",raw,152,0,0,0,0,2,0,0,0x0c02)
        report=inspect_source(bytes(raw))
        self.assertEqual(report["index_descriptors"][0]["declared_indices"],6)
        self.assertFalse(report["geometry_binding_export_allowed"])
        self.assertFalse(report["original_index_buffer_recovered"])
if __name__=="__main__":unittest.main()
