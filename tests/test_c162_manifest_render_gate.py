import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c162_manifest_render_gate import validate_manifest

def manifest():
    return {"schema":"p3d-source-draw-pass-v1","sampler_roles_verified":False,
            "native_renderer_integrated":False,"mesh_count":1,
            "draws":[{"order":0,"mesh":0,"material":3,"triangles":2,"pass":"secondary"}],
            "secondary_only_meshes":[0]}

class C162Tests(unittest.TestCase):
    def test_secondary_only(self):
        self.assertEqual(validate_manifest(manifest())["secondary_only_meshes"],[0])
    def test_false_sampler_claim(self):
        m=manifest();m["sampler_roles_verified"]=True
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_false_renderer_claim(self):
        m=manifest();m["native_renderer_integrated"]=True
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_invalid_order(self):
        m=manifest();m["draws"][0]["order"]=1
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_invented_primary(self):
        m=manifest();m["draws"][0]["pass"]="primary"
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_bad_material(self):
        m=manifest();m["draws"][0]["material"]=256
        with self.assertRaises(ValueError):validate_manifest(m)
if __name__=="__main__":unittest.main()
