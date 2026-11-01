import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c171_verified_primitive_gate import verify,SCHEMA

def valid():
    return {"schema":SCHEMA,"source":"original-c5",
            "method":"verified-original-primitive-order",
            "verified_by":"source-decoder-crosscheck",
            "meshes":[{"model":"p000","mesh":0,"triangles":[[0,1,2]]}]}

class C171Tests(unittest.TestCase):
    def test_verified_mapping(self):
        self.assertEqual(verify(valid())["verified_triangles"],1)
    def test_descriptor_only_rejected(self):
        d=valid();d["method"]="descriptor-count-inference"
        with self.assertRaises(ValueError):verify(d)
    def test_unverified_provenance_rejected(self):
        d=valid();d["verified_by"]="float-heuristic"
        with self.assertRaises(ValueError):verify(d)
    def test_degenerate_triangle_rejected(self):
        d=valid();d["meshes"][0]["triangles"]=[[1,1,2]]
        with self.assertRaises(ValueError):verify(d)
if __name__=="__main__":unittest.main()
