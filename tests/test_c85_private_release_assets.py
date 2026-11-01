"""C85 release gate tests use synthetic input only, never Nintendo payloads."""
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_private_release_assets import Assets,audit,MODEL_IDS

class C85Tests(unittest.TestCase):
    def test_expected_recovered_roster(self):
        self.assertEqual(len(MODEL_IDS),730)
        self.assertIn(733,MODEL_IDS)
        for gap in (721,722,723,724):
            self.assertNotIn(gap,MODEL_IDS)
    def test_missing_private_asset_lists_blockers(self):
        with tempfile.TemporaryDirectory() as folder:
            src=Assets(pathlib.Path(folder))
            result=audit(src);src.close()
            self.assertFalse(result["asset_complete"])
            self.assertEqual(result["counts"]["mesh_previews"],0)
            self.assertIn("ui/pages/t0_10_records.rgb555",result["missing"])
            self.assertIn("ui/pages/t1_10_records.rgb555",result["missing"])
            self.assertGreater(len(result["missing"]),10)
            self.assertFalse(result["visual_accuracy_verified"])
    def test_zip_root_and_source_header_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            zip_path=pathlib.Path(folder)/"stage.zip"
            with zipfile.ZipFile(zip_path,"w") as z:
                z.writestr("data/dex_en.p3dx",struct.pack("<4sHH",b"P3DX",1,649)+bytes(649*256))
                z.writestr("ui/pages/t0_00_home.rgb555",bytes(256*192*2))
                z.writestr("moves.p3dm",b"BADM"+bytes(4000))
            src=Assets(zip_path)
            result=audit(src);src.close()
            self.assertFalse(any("data/dex_en.p3dx" in msg for msg in result["invalid"]))
            self.assertTrue(any("moves.p3dm" in msg for msg in result["invalid"]))
            self.assertEqual(result["counts"]["original_derived_texture_payloads"],0)
    def test_release_never_claims_partial_game_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,str(ROOT/"tools"/"check_private_release_assets.py"),
                      "--root",folder,"--release"],text=True,capture_output=True)
            self.assertEqual(result.returncode,1)
            self.assertIn("BLOCKED",result.stderr)
    def test_audit_mode_returns_report(self):
        with tempfile.TemporaryDirectory() as folder:
            output=pathlib.Path(folder)/"report.json"
            result=subprocess.run([sys.executable,str(ROOT/"tools"/"check_private_release_assets.py"),
                     "--root",folder,"--report",str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(json.loads(output.read_text())["asset_complete"])

if __name__=="__main__":
    unittest.main()
