"""C85 release gate tests use synthetic input only, never Nintendo payloads."""
import json
import pathlib
import struct
import zlib
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
            self.assertIn("ui/pages/t1_01_dex_overlay.rgb555",result["missing"])
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
    def test_original_3d_hud_mask_requires_both_opacity_states(self):
        with tempfile.TemporaryDirectory() as folder:
            p=pathlib.Path(folder)
            overlay=p/"ui/pages/t1_01_dex_overlay.rgb555"
            overlay.parent.mkdir(parents=True)
            overlay.write_bytes(bytes((0x34,0x92))*(256*192))
            src=Assets(p)
            result=audit(src)
            src.close()
            self.assertTrue(any("t1_01_dex_overlay.rgb555" in x for x in result["invalid"]))
            overlay.write_bytes(bytes((0,0))*(256*192))
            src=Assets(p)
            result=audit(src)
            src.close()
            self.assertTrue(any("t1_01_dex_overlay.rgb555" in x for x in result["invalid"]))
            overlay.write_bytes(bytes((0,0)) + bytes((0x34,0x92))*(256*192-1))
            src=Assets(p)
            result=audit(src)
            src.close()
            self.assertFalse(any("t1_01_dex_overlay.rgb555" in x for x in result["invalid"]))

    def test_original_C5_source_provenance_sidecar(self):
        with tempfile.TemporaryDirectory() as folder:
            p=pathlib.Path(folder)
            sidecar=p/"materials/p000.p3mr"
            sidecar.parent.mkdir(parents=True)
            ranges=struct.pack("<6H",0,2,10,2,7,0x0c02)+struct.pack(
                "<6H",2,1,12,7,65535,0x0c02)
            valid=struct.pack("<4s4HI",b"P3MR",1,0,3,2,zlib.crc32(ranges))+ranges
            sidecar.write_bytes(valid)
            src=Assets(p)
            result=audit(src)
            src.close()
            self.assertEqual(result["counts"]["source_C5_material_provenance"],1)
            self.assertFalse(any("p000.p3mr" in x for x in result["invalid"]))
            self.assertFalse(result["asset_complete"])
            sidecar.write_bytes(valid[:-1]+bytes([valid[-1]^1]))
            src=Assets(p)
            result=audit(src)
            src.close()
            self.assertTrue(any("p000.p3mr" in x for x in result["invalid"]))
            sidecar.write_bytes(valid.replace(b"P3MR",b"P3MT",1))
            src=Assets(p)
            result=audit(src)
            src.close()
            self.assertTrue(any("p000.p3mr" in x for x in result["invalid"]))

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
