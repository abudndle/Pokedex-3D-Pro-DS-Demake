import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c164_private_geometry_binding import build_verified_binding

def manifest():
    return {"schema":"p3d-source-draw-pass-v1","model_id":"p001","mesh_count":1,
            "draws":[{"order":0,"mesh":0,"material":0,"pass":"primary","triangles":2}],
            "secondary_only_meshes":[],"sampler_roles_verified":False,"native_renderer_integrated":False}
def evidence():
    return {"schema":"p3d-geometry-evidence-v1","model_id":"p001","verified":True,
            "source_order_method":"original-index-buffer",
            "bindings":[{"draw_order":0,"first_triangle":0,"triangle_count":2,"source_order_verified":True}]}
class C164Tests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(build_verified_binding(manifest(),evidence(),2)["triangle_count"],2)
    def test_no_proof(self):
        e=evidence();e["verified"]=False
        with self.assertRaises(ValueError):build_verified_binding(manifest(),e,2)
    def test_wrong_model(self):
        e=evidence();e["model_id"]="p002"
        with self.assertRaises(ValueError):build_verified_binding(manifest(),e,2)
    def test_unsupported_method(self):
        e=evidence();e["source_order_method"]="guess"
        with self.assertRaises(ValueError):build_verified_binding(manifest(),e,2)
    def test_unassigned_triangles(self):
        with self.assertRaises(ValueError):build_verified_binding(manifest(),evidence(),3)
if __name__=="__main__":unittest.main()
