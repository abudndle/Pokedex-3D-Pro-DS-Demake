"""C95 clean synthetic original-triangle selection and preview quality gate."""
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c95_original_source_lod_quality import select_source_faces,audit

def fixture(root):
    stage=root/"test.zip"
    report=root/"test.json"
    ds=struct.pack("<4sHHII",b"DS3M",2,1,3,2)+bytes(21)
    uv=struct.pack("<4sHH",b"P3UV",1,1)+bytes(12)
    material=struct.pack("<4sHH4H",b"P3MT",1,1,0,1,0,0)
    manifest=struct.pack("<4sHH4H",b"P3TX",1,1,0,8,8,1)
    texture=struct.pack("<4sHHH",b"P3PX",2,8,8)+bytes(128)
    with zipfile.ZipFile(stage,"w") as z:
        z.writestr("README_EXPERIMENTAL_PRIVATE_C92.txt","Original GPU sampler not verified")
        rootname="diagnostic_nitrofs/"
        for path,content in [
            ("preview/p000.ds3m",ds),("preview/p000.p3uv",uv),
            ("materials/p000.p3mt",material),("materials/p000.p3tx",manifest),
            ("textures/p000/t000.p3px",texture)]:
            z.writestr(rootname+path,content)
    data={"summary":{"models":1,"source_triangles":2,
                     "original_gpu_sampler_roles_proven":False,
                     "native_visual_accuracy_verified":False},
          "models":[{"model_id":"p000","original_mesh_groups":1,
                     "native_triangles":1,"original_triangles":2,
                     "material_ranges":1,"area_retention_new":0.9,
                     "area_retention_midpoint":0.4,
                     "mesh_material_reference":"C90_VERIFIED",
                     "gpu_color_sampler_role":"C92_PROVISIONAL",
                     "native_model_visual_fidelity_certified":False}]}
    report.write_text(json.dumps(data))
    return stage,report

class C95Quality(unittest.TestCase):
    def test_area_max_uses_original_faces(self):
        verts=[(0,0,0),(1,0,0),(0,1,0),(4,0,0),(0,4,0)]
        indices,improved,baseline,total=select_source_faces(
            verts,[(0,1,2),(0,3,4)],1)
        self.assertEqual(indices,[1])
        self.assertEqual((improved,total),(16,17))
        self.assertGreaterEqual(improved,baseline)
    def test_order_is_stable(self):
        verts=[(0,0,0),(1,0,0),(0,1,0),(2,0,0),(0,2,0)]
        faces=[(0,1,2),(0,3,4)]*8
        indices,improved,prior,_=select_source_faces(verts,faces,6)
        self.assertEqual(len(indices),6)
        self.assertEqual(indices,sorted(set(indices)))
        self.assertGreaterEqual(improved,prior)
    def test_invalid_quota_rejected(self):
        verts=[(0,0,0),(1,0,0),(0,1,0)]
        with self.assertRaisesRegex(ValueError,"budget"):
            select_source_faces(verts,[(0,1,2)]*601,601)
    def test_degenerate_original_face_stratum_rejected(self):
        verts=[(0,0,0),(1,0,0),(2,0,0)]
        with self.assertRaisesRegex(ValueError,"nondegenerate"):
            select_source_faces(verts,[(0,1,2)],1)
    def test_private_diagnostic_can_pass_without_release_approval(self):
        with tempfile.TemporaryDirectory() as d:
            stage,report=fixture(pathlib.Path(d))
            result=audit(stage,report)
            self.assertEqual(result["ds_preview_triangles"],1)
            self.assertFalse(result["normal_release_approved"])
            self.assertFalse(result["native_visual_parity_verified"])
            with self.assertRaisesRegex(ValueError,"incomplete"):
                audit(stage,report,True)
    def test_fabricated_original_shader_claim_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            stage,report=fixture(pathlib.Path(d))
            payload=json.loads(report.read_text())
            payload["summary"]["original_gpu_sampler_roles_proven"]=True
            report.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"cannot be inferred"):
                audit(stage,report)
    def test_regressing_source_area_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            stage,report=fixture(pathlib.Path(d))
            payload=json.loads(report.read_text())
            payload["models"][0]["area_retention_new"]=0.1
            report.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"retention"):
                audit(stage,report)

if __name__=="__main__":unittest.main()
