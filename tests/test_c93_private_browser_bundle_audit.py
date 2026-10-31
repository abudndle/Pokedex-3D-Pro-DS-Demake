"""Synthetic C93 offline browser model provenance tests; no Nintendo assets."""
import base64
import hashlib
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c93_private_browser_bundle_audit import audit

def fixture(folder, corrupt=False):
    ds=struct.pack("<4sHHII",b"DS3M",2,1,3,1)+bytes(21)
    uv=struct.pack("<4sHH",b"P3UV",1,1)+bytes(12)
    mat=struct.pack("<4sHH4H",b"P3MT",1,1,0,1,0,0)
    pixels=struct.pack("<4sHHH",b"P3PX",2,8,8)+bytes([255,255])*64
    raw=struct.pack("<4I",len(ds),len(uv),len(mat),1)+ds+uv+mat
    raw+=struct.pack("<HI",0,len(pixels))+pixels
    compressed=zlib.compress(raw)
    provenance={"model_count":1,"native_3ds_shader_equivalence_verified":False,
        "original_sampler_channels_proven":False,
        "models":{"p000":{"compressed_sha256":hashlib.sha256(compressed).hexdigest(),
            "uncompressed_sha256":hashlib.sha256(raw).hexdigest(),
            "geometry_mode":"600_FACE_DS_SOURCE_SAMPLE",
            "source_file_sha256":{key:hashlib.sha256(value).hexdigest()
                for key,value in (("ds3m",ds),("p3uv",uv),("p3mt",mat),("t000.p3px",pixels))}}}}
    encoded=base64.b64encode(compressed).decode()
    if corrupt:encoded=('A' if encoded[0]!='A' else 'B')+encoded[1:]
    html=folder/"fixture.html"
    html.write_text("const MODEL_PAYLOADS="+json.dumps({"p000":encoded})+
                    ";\nconst ids=Object.keys(MODEL_PAYLOADS);")
    report=folder/"fixture.json"
    report.write_text(json.dumps(provenance))
    return html,report

class C93BrowserTests(unittest.TestCase):
    def test_synthetic_source_provenance_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            html,report=fixture(pathlib.Path(directory))
            data=audit(html,report)
            self.assertEqual(data["models"],1)
            self.assertEqual(data["total_display_triangles"],1)
            self.assertEqual(data["source_derived_images"],1)
            self.assertFalse(data["original_shader_3ds_fidelity_proven"])
    def test_tampered_embedded_asset_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            html,report=fixture(pathlib.Path(directory),corrupt=True)
            with self.assertRaisesRegex(ValueError,"hash mismatch"):audit(html,report)
    def test_unfounded_original_shader_claim_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            html,report=fixture(pathlib.Path(directory))
            data=json.loads(report.read_text())
            data["original_sampler_channels_proven"]=True
            report.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"unsubstantiated"):audit(html,report)
    def test_missing_entire_model_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            html,report=fixture(pathlib.Path(directory))
            data=json.loads(report.read_text())
            data["models"]["p001"]=data["models"]["p000"]
            report.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"roster"):audit(html,report)
if __name__=="__main__":unittest.main()
