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
            self.assertIn("ui/title/t0_title.rgb555",result["missing"])
            self.assertIn("ui/title/t1_title.rgb555",result["missing"])
            self.assertFalse(result["original_title_screen_visually_verified"])
            self.assertIn("source_C5_shader_capabilities: 730 model resources not staged",result["missing"])
            self.assertIn("source_C5_operation_words: 730 model resources not staged",result["missing"])
            self.assertFalse(result["original_shader_sampler_roles_verified"])
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
    def test_original_title_requires_both_independent_original_frames(self):
        with tempfile.TemporaryDirectory() as folder:
            p=pathlib.Path(folder)
            d=p/"ui/title"
            d.mkdir(parents=True)
            bottom=d/"t0_title.rgb555"
            top=d/"t1_title.rgb555"
            bottom.write_bytes(bytes((0x21,0x9b))*(256*192))
            src=Assets(p);report=audit(src);src.close()
            self.assertIn("ui/title/t1_title.rgb555",report["missing"])
            self.assertFalse(report["asset_complete"])
            top.write_bytes(bytes((0xab,0xd4))*(256*192))
            src=Assets(p);report=audit(src);src.close()
            self.assertFalse(any("ui/title/" in x for x in report["missing"]+report["invalid"]))
            self.assertFalse(report["original_title_screen_visually_verified"])
            top.write_bytes(b"short")
            src=Assets(p);report=audit(src);src.close()
            self.assertTrue(any("ui/title/t1_title.rgb555" in x for x in report["invalid"]))

    def test_private_source_timed_title_animation_must_be_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            title=root/"ui/title"
            title.mkdir(parents=True)
            for screen in (0,1):
                (title/f"t{screen}_title.rgb555").write_bytes(
                    bytes((0x21,0x9b))*(256*192))
                (title/f"t{screen}_01_title.rgb555").write_bytes(
                    bytes((0x33,0x91))*(256*192))
            timeline=title/"timeline.p3tl"
            payload=struct.pack("<4H",0,2,1,3)
            good=struct.pack("<4s4HI",b"P3TL",1,2,0,0,
                             zlib.crc32(payload))+payload
            timeline.write_bytes(good)
            src=Assets(root);valid=audit(src);src.close()
            self.assertFalse(any("timeline.p3tl" in x for x in valid["invalid"]))
            self.assertFalse(any("t1_01_title.rgb555" in x for x in valid["missing"]))
            self.assertFalse(valid["original_title_screen_visually_verified"])
            # A missing upper frame cannot be silently replaced by lower art.
            (title/"t1_01_title.rgb555").unlink()
            src=Assets(root);missing=audit(src);src.close()
            self.assertIn("ui/title/t1_01_title.rgb555",missing["missing"])
            (title/"t1_01_title.rgb555").write_bytes(bytes((0,0))*(256*192))
            for broken in (good[:-1],good[:-1]+bytes([good[-1]^1]),
                           good[:4]+struct.pack("<H",2)+good[6:]):
                timeline.write_bytes(broken)
                src=Assets(root);invalid=audit(src);src.close()
                self.assertTrue(any("timeline.p3tl" in x for x in invalid["invalid"]))

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

    def test_original_C5_shader_capability_sidecar(self):
        with tempfile.TemporaryDirectory() as folder:
            p=pathlib.Path(folder)
            sidecar=p/"materials/p000.p3sc"
            sidecar.parent.mkdir(parents=True)
            records=(struct.pack("<5H",0,3,2,65535,1)+
                     struct.pack("<5H",1,4,7,65535,2))
            good=struct.pack("<4s4HI",b"P3SC",2,0,2,0,zlib.crc32(records))+records
            sidecar.write_bytes(good)
            src=Assets(p)
            report=audit(src)
            src.close()
            self.assertEqual(report["counts"]["source_C5_shader_capabilities"],1)
            self.assertFalse(any("p000.p3sc" in x for x in report["invalid"]))
            self.assertFalse(report["original_shader_sampler_roles_verified"])
            # Legacy v1 loses all CF_* flags except COLOR/BUMP.
            legacy=bytearray(good)
            struct.pack_into("<H",legacy,4,1)
            sidecar.write_bytes(legacy)
            src=Assets(p)
            legacy_report=audit(src)
            src.close()
            self.assertTrue(any("p000.p3sc" in x for x in legacy_report["invalid"]))
            # P3SC v2 faithfully carries the OTHER declaration bit.
            declared_other=bytearray(good)
            struct.pack_into("<H",declared_other,16+8,5)
            struct.pack_into("<I",declared_other,12,zlib.crc32(declared_other[16:]))
            sidecar.write_bytes(declared_other)
            src=Assets(p)
            other_report=audit(src)
            src.close()
            self.assertFalse(any("p000.p3sc" in x for x in other_report["invalid"]))
            sidecar.write_bytes(good[:-1]+bytes([good[-1]^1]))
            src=Assets(p)
            report=audit(src)
            src.close()
            self.assertTrue(any("p000.p3sc" in x for x in report["invalid"]))
            # Even a valid CRC does not excuse an unknown shader role flag.
            bad=bytearray(good)
            struct.pack_into("<H",bad,16+8,0x8000)
            struct.pack_into("<I",bad,12,zlib.crc32(bad[16:]))
            sidecar.write_bytes(bad)
            src=Assets(p)
            report=audit(src)
            src.close()
            self.assertTrue(any("p000.p3sc" in x for x in report["invalid"]))

    def test_original_c5_material_operation_words(self):
        # P3SW v1 carries original 13-word material records, not sampler roles.
        with tempfile.TemporaryDirectory() as folder:
            p=pathlib.Path(folder)
            sidecar=p/"materials/p000.p3sw"
            sidecar.parent.mkdir(parents=True)
            one=struct.pack("<13I",0,0xffff0002,*([0]*11))
            two=struct.pack("<13I",1,0xffff0007,*([0]*11))
            body=one+two
            good=struct.pack("<4s4HI",b"P3SW",1,0,2,0,zlib.crc32(body))+body
            sidecar.write_bytes(good)
            src=Assets(p)
            report=audit(src)
            src.close()
            self.assertEqual(report["counts"]["source_C5_operation_words"],1)
            self.assertFalse(any("p000.p3sw" in x for x in report["invalid"]))
            self.assertFalse(report["original_shader_sampler_roles_verified"])
            for corrupt in (
                good[:-1],
                good+b"\\x00",
                good[:6]+struct.pack("<H",1)+good[8:],
                good[:4]+struct.pack("<H",2)+good[6:],
                good[:-1]+bytes([good[-1]^1]),
            ):
                sidecar.write_bytes(corrupt)
                src=Assets(p)
                report=audit(src)
                src.close()
                self.assertTrue(any("p000.p3sw" in x for x in report["invalid"]))

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
