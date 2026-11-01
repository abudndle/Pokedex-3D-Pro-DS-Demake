import importlib.util
import pathlib
import struct
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("c180",ROOT/"tools/c180_private_c5_coverage.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class C180Coverage(unittest.TestCase):
    def fixture(self):
        data=bytearray(0x90)
        data[:2]=b"\xc5\x78"
        struct.pack_into("<H",data,0x14,1)
        struct.pack_into("<I",data,0x3c,0x78)
        struct.pack_into("<I",data,0x40,0x8c)
        struct.pack_into("<I",data,0x44,0x8c)
        struct.pack_into("<5I",data,0x78,0x8c,0,0x00040001,0,0)
        return data
    def test_valid_structural_fixture(self):
        result=mod.inspect(self.fixture())
        self.assertEqual(result["primary"],1)
        self.assertFalse(result["vertex_semantics_verified"])
    def test_reject_invalid_table_bounds(self):
        data=self.fixture()
        struct.pack_into("<I",data,0x40,0x80)
        with self.assertRaises(ValueError):mod.inspect(data)
    def test_report_invalid_payload(self):
        data=self.fixture()
        struct.pack_into("<I",data,0x78,0xffffffff)
        self.assertTrue(mod.inspect(data)["structural_errors"])
if __name__=="__main__":unittest.main()
