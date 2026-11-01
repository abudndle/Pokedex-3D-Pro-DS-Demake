import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c163_geometry_draw_gate import validate_geometry_binding

def m():
    return {"schema":"p3d-source-draw-pass-v1","sampler_roles_verified":False,
        "native_renderer_integrated":False,"mesh_count":1,
        "draws":[{"order":0,"mesh":0,"material":0,"triangles":2,"pass":"secondary"}],
        "secondary_only_meshes":[0]}
def b():
    return [{"draw_order":0,"first_triangle":0,"triangle_count":2,"source_order_verified":True}]
class C163Tests(unittest.TestCase):
    def test_verified_range(self):
        self.assertEqual(validate_geometry_binding(m(),b(),2)["triangles_bound"],2)
    def test_missing_binding(self):
        with self.assertRaises(ValueError):validate_geometry_binding(m(),[],2)
    def test_unverified_order(self):
        x=b();x[0]["source_order_verified"]=False
        with self.assertRaises(ValueError):validate_geometry_binding(m(),x,2)
    def test_out_of_bounds(self):
        x=b();x[0]["first_triangle"]=1
        with self.assertRaises(ValueError):validate_geometry_binding(m(),x,2)
    def test_wrong_face_count(self):
        x=b();x[0]["triangle_count"]=1
        with self.assertRaises(ValueError):validate_geometry_binding(m(),x,2)
if __name__=="__main__":unittest.main()
