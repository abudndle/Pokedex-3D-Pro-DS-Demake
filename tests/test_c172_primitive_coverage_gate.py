import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c172_primitive_coverage_gate import verify_coverage
from c171_verified_primitive_gate import SCHEMA

def fixture():
    source=bytearray(276)
    source[:2]=bytes((0xc5,0x78))
    struct.pack_into("<H",source,0x10,1)
    struct.pack_into("<HH",source,0x14,1,1)
    struct.pack_into("<3I",source,0x3c,120,140,152)
    struct.pack_into("<5I",source,120,152,0,4|(28<<16),0,0)
    struct.pack_into("<3I",source,140,264,0,6|(2<<16))
    manifest={"schema":SCHEMA,"source":"original-c5",
              "method":"verified-original-primitive-order",
              "verified_by":"source-decoder-crosscheck","model":"p000",
              "meshes":[{"model":"p000","mesh":0,
                         "triangles":[[0,1,2],[1,2,3]]}]}
    return manifest,bytes(source)
class C172Tests(unittest.TestCase):
    def test_full_coverage(self):
        m,s=fixture()
        self.assertEqual(verify_coverage(m,s)["verified_triangles"],2)
    def test_partial_coverage_rejected(self):
        m,s=fixture();m["meshes"][0]["triangles"].pop()
        with self.assertRaises(ValueError):verify_coverage(m,s)
    def test_out_of_range_vertex_rejected(self):
        m,s=fixture();m["meshes"][0]["triangles"][0]=[0,1,4]
        with self.assertRaises(ValueError):verify_coverage(m,s)
    def test_cross_model_rejected(self):
        m,s=fixture();m["model"]="p001"
        with self.assertRaises(ValueError):verify_coverage(m,s)
if __name__=="__main__":unittest.main()
