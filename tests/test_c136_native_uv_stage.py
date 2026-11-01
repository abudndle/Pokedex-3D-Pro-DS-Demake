"""C136 synthetic private-native DS3M/UV staging regression."""
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from c136_native_uv_stage import ROSTER, build, native_model, validate_uv


def ds3m(reserved=11, triangles=1):
    return (struct.pack("<4sHHII", b"DS3M", 2, triangles, reserved, triangles+3)
            + struct.pack("<" + "h" * (triangles*9), *([0, 0, 0, 4096, 0, 0,
                                                        0, 4096, 0] * triangles))
            + bytes((192, 224, 232)) * triangles)


def uv(coords):
    return struct.pack("<4sHH", b"P3UV", 1, 1) + struct.pack("<6h", *coords)


def fixture(root):
    base = root/"base.zip"
    candidates = root/"candidates.zip"
    report = root/"c86.json"
    with zipfile.ZipFile(base,"w") as z:
        for model in sorted(ROSTER):
            z.writestr(f"preview/p{model:03d}.ds3m",ds3m())
        z.writestr("moves.p3dm",b"unmodified synthetic fixture")
    with zipfile.ZipFile(candidates,"w") as z:
        for model,coords in (
            (9,(0,0,4096,0,0,4096)),
            (40,(-1,0,4096,0,0,4096)),
            (45,(0,0,4096,0,0,4096)),
        ):
            z.writestr(f"uv_candidates/p{model:03d}.ds3m",ds3m(reserved=24))
            z.writestr(f"uv_candidates/p{model:03d}.p3uv",uv(coords))
    report.write_text(json.dumps({"per_model":[
        {"model_id":f"p{model:03d}",
         "source":"C7 earlier inferred UV candidate" if model==45
         else "C62 complete source-derived candidate"}
        for model in sorted(ROSTER)]}))
    return base,candidates,report


class C136Tests(unittest.TestCase):
    def test_native_header_repairs_historical_source_vertex_field(self):
        restored, info = native_model(ds3m(reserved=418))
        self.assertEqual(struct.unpack_from("<I",restored,8)[0],0)
        self.assertEqual(struct.unpack_from("<I",restored,12)[0],4)
        self.assertEqual(info["historical_source_vertices"],418)
        self.assertEqual(restored[16:],ds3m(reserved=418)[16:])

    def test_baseline_does_not_enable_any_uvs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b,manifest=fixture(root)
            out=root/"baseline.zip"
            stats=build(a,b,out,mode="baseline",source_report=manifest)
            self.assertEqual(stats["native_compatible_preview_models"],730)
            self.assertEqual(stats["activated_paired_unit_uv_qa"],0)
            self.assertEqual(stats["source_unit_uv_candidates"],1)
            with zipfile.ZipFile(out) as z:
                self.assertEqual(struct.unpack_from("<I",z.read("preview/p000.ds3m"),8)[0],0)
                self.assertFalse(any(x.endswith(".p3uv") for x in z.namelist()))
                self.assertEqual(z.read("moves.p3dm"),b"unmodified synthetic fixture")

    def test_qa_installs_both_exact_paired_files_only_for_c62_unit_uvs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b,manifest=fixture(root)
            out=root/"qa.zip"
            stats=build(a,b,out,mode="unit-uv-qa",source_report=manifest)
            self.assertEqual(stats["activated_paired_unit_uv_qa"],1)
            self.assertFalse(stats["original_3ds_visual_parity_proven"])
            with zipfile.ZipFile(out) as z:
                self.assertEqual(struct.unpack_from("<I",z.read("preview/p009.ds3m"),8)[0],0)
                self.assertIn("preview/p009.p3uv",z.namelist())
                self.assertNotIn("preview/p040.p3uv",z.namelist())
                self.assertNotIn("preview/p045.p3uv",z.namelist())
                self.assertEqual(struct.unpack_from("<I",z.read("preview/p009.ds3m"),8)[0],0)

    def test_reject_malformed_and_unpaired_uv(self):
        with self.assertRaisesRegex(ValueError,"P3UV"):
            validate_uv(uv((0,0,4096,0,0,4096))[:-2],1)
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b,manifest=fixture(root)
            with zipfile.ZipFile(b,"a") as z:
                z.writestr("uv_candidates/p046.ds3m",ds3m())
            with self.assertRaisesRegex(ValueError,"pair missing"):
                build(a,b,root/"invalid.zip",source_report=manifest)

    def test_requires_complete_original_roster_and_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b,manifest=fixture(root)
            with self.assertRaisesRegex(ValueError,"provenance"):
                build(a,b,root/"noprov.zip",mode="unit-uv-qa")
            with self.assertRaisesRegex(ValueError,"never overwrite"):
                build(a,b,a,source_report=manifest)


if __name__ == "__main__":
    unittest.main()
