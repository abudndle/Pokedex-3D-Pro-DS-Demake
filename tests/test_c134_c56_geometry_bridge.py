"""C134: synthetic cross-stage C56 SHA/structure/C86 readiness regression."""
import csv
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from audit_c134_c56_geometry_bridge import verify, EXPECTED_IDS, PART_RANGES, WARNING_IDS
from test_c133_c56_decoder import synthetic_c5


def make_fixtures(base):
    parts=[]
    csvrows=[]
    for index,(low,high) in enumerate(PART_RANGES):
        part=base / f"part{index+1}.zip"
        with zipfile.ZipFile(part,"w",compression=zipfile.ZIP_DEFLATED) as out:
            for model in range(low,high+1):
                if model not in EXPECTED_IDS:
                    continue
                label=f"p{model:03d}"
                warning=model in WARNING_IDS
                blob=synthetic_c5(reserved1=0x26 if warning else 0)
                out.writestr(f"decoded_c5/{label}.c5",blob)
                csvrows.append({
                    "model":label,
                    "status":"valid_with_0x26_flag_warning" if warning else "strict_valid",
                    "decoded_bytes":str(len(blob)),
                    "0x26_descriptor_flags":"1" if warning else "0",
                    "primary_descriptor_count":"1",
                    "sha256":hashlib.sha256(blob).hexdigest(),"error":""})
        parts.append(part)
    bundle=base/"decoder_tools.zip"
    with zipfile.ZipFile(bundle,"w") as z:
        import io
        output=io.StringIO()
        writer=csv.DictWriter(output,fieldnames=list(csvrows[0]))
        writer.writeheader()
        writer.writerows(csvrows)
        z.writestr("C56_validation.csv",output.getvalue())
    geometry=base/"c86.json"
    records=[]
    for model in sorted(EXPECTED_IDS):
        records.append({"model_id":f"p{model:03d}",
                        "fallback_preview":model not in (730,731,732,733),
                        "paired_uv_candidate":model<538})
    geometry.write_text(json.dumps({
        "source_model_records":730,"source_derived_fallback_ds3m":726,
        "complete_uv_paired_candidates":538,"missing_c18_meshes":4,
        "per_model":records}))
    return parts,bundle,geometry


class C134Tests(unittest.TestCase):
    def test_complete_synthetic_sha_and_geometry_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            parts,bundle,geometry=make_fixtures(pathlib.Path(tmp))
            r=verify(parts,bundle,geometry)
            self.assertTrue(r["private_integrity_check_passed"])
            self.assertEqual(r["c56_c5_verified"],730)
            self.assertEqual(r["c56_strict"],723)
            self.assertEqual(len(r["c56_descriptor_warnings"]),7)
            self.assertEqual(r["c86_fallback_ds3m"],726)
            self.assertEqual(r["c86_paired_uv_candidates"],538)
            self.assertEqual(r["c86_missing_fallback_geometry"],
                             ["p730","p731","p732","p733"])
            self.assertEqual(r["production_renderer_ready"],0)
            self.assertFalse(any(x["verified_material_binding"] for x in r["per_model"]))

    def test_detect_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            parts,bundle,geometry=make_fixtures(pathlib.Path(tmp))
            part=parts[0]
            with zipfile.ZipFile(part) as z:
                entries={name:z.read(name) for name in z.namelist()}
            entries["decoded_c5/p000.c5"]+=b"x"
            with zipfile.ZipFile(part,"w") as z:
                for name,data in entries.items():
                    z.writestr(name,data)
            with self.assertRaisesRegex(ValueError,"SHA/size mismatch"):
                verify(parts,bundle,geometry)

    def test_reject_missing_geometry_and_unexpected_uv(self):
        with tempfile.TemporaryDirectory() as tmp:
            parts,bundle,geometry=make_fixtures(pathlib.Path(tmp))
            report=json.loads(geometry.read_text())
            report["per_model"].pop()
            geometry.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,"report missing"):
                verify(parts,bundle,geometry)
            report["per_model"].append({"model_id":"p733",
                "fallback_preview":False,"paired_uv_candidate":True})
            geometry.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,"candidate has no"):
                verify(parts,bundle,geometry)

    def test_archive_part_order_is_essential(self):
        with tempfile.TemporaryDirectory() as tmp:
            parts,bundle,geometry=make_fixtures(pathlib.Path(tmp))
            with self.assertRaisesRegex(ValueError,"displaced"):
                verify(parts[::-1],bundle,geometry)


if __name__=="__main__":
    unittest.main()
