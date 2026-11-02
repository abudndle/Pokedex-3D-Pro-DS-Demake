"""C288 synthetic raw C111/C275/C287 material/draw crosschecks."""
import copy
import hashlib
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c288_private_shader_material_gate import reconcile, load_evidence


def fixture():
    words = [3, 0xffff0002] + [0] * 11
    material = {"material_index": 0, "shader_index": 3,
                "shader_declaration": "sample;;;CF_COLORMAP",
                "source_material_name": "synthetic", "source_texture_references": [2, 65535],
                "source_material_words_hex": [f"0x{x:08x}" for x in words],
                "source_material_record_sha256": hashlib.sha256(struct.pack("<13I", *words)).hexdigest()}
    sha = "a" * 64
    c111 = {"p000": {"schema": "C111_ORIGINAL_C5_MATERIAL_WORDS_V1",
                      "model_id": "p000", "source_C5_sha256": sha,
                      "material_count": 1, "evidence": [material],
                      "original_GPU_sampler_roles_verified": 0}}
    c275 = {"summary": {"schema": "C275_PRIVATE_C5_DRAW_MATERIAL_REFERENCE_V1"},
            "models": [{"model_id": "p000", "source_c5_sha256": sha, "material_count": 1,
                        "draws": [{"draw_index": 0, "mesh_index": 0, "material_index": 0,
                                   "shader_index": 3, "shader_declaration": material["shader_declaration"],
                                   "source_material_name": "synthetic",
                                   "source_texture_reference_indices": [2, 65535]}]}]}
    c287 = {"summary": {"schema": "C287_PRIVATE_DRAW_TO_SOURCE_TEXTURE_CHAIN_V1"},
            "models": [{"model_id": "p000", "source_c5_sha256": sha,
                        "draws": [{"draw_index": 0, "mesh_index": 0, "material_index": 0,
                                   "source_draw_material_reference_verified": True,
                                   "gpu_sampler_verified": False, "native_p3px_binding_verified": False,
                                   "texture_reference_slots": [
                                       {"slot": 0, "source_texture_index": 2, "gpu_sampler_verified": False,
                                        "native_p3px_binding_verified": False},
                                       {"slot": 1, "source_texture_index": None, "status": "SOURCE_REFERENCE_ABSENT",
                                        "gpu_sampler_verified": False, "native_p3px_binding_verified": False}]}]}]}
    return c275, c287, c111


class GateTests(unittest.TestCase):
    def test_source_crosscheck_keeps_sampler_unverified(self):
        report = reconcile(*fixture())
        self.assertEqual(report["summary"]["draws_checked"], 1)
        self.assertEqual(report["summary"]["source_texture_reference_slots_checked"], 1)
        self.assertEqual(report["summary"]["original_gpu_sampler_roles_verified"], 0)
        self.assertFalse(report["summary"]["release_ready"])

    def test_source_sha_mismatch(self):
        a, b, c = fixture()
        b["models"][0]["source_c5_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "source C5 SHA"):
            reconcile(a, b, c)

    def test_forged_raw_word_hash(self):
        a, b, c = fixture()
        c["p000"]["evidence"][0]["source_material_words_hex"][2] = "0x00000001"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            reconcile(a, b, c)

    def test_mismatched_shader(self):
        a, b, c = fixture()
        a["models"][0]["draws"][0]["shader_index"] = 4
        with self.assertRaisesRegex(ValueError, "raw C111"):
            reconcile(a, b, c)

    def test_mismatched_source_texture_reference(self):
        a, b, c = fixture()
        a["models"][0]["draws"][0]["source_texture_reference_indices"] = [1, 65535]
        with self.assertRaisesRegex(ValueError, "raw C111"):
            reconcile(a, b, c)

    def test_mismatched_bridge_texture_slot(self):
        a, b, c = fixture()
        b["models"][0]["draws"][0]["texture_reference_slots"][0]["source_texture_index"] = 1
        with self.assertRaisesRegex(ValueError, "slot mismatch"):
            reconcile(a, b, c)

    def test_forged_gpu_sampler_claim(self):
        a, b, c = fixture()
        b["models"][0]["draws"][0]["gpu_sampler_verified"] = True
        with self.assertRaisesRegex(ValueError, "unverified sampler"):
            reconcile(a, b, c)

    def test_duplicate_draw(self):
        a, b, c = fixture()
        a["models"][0]["draws"].append(copy.deepcopy(a["models"][0]["draws"][0]))
        b["models"][0]["draws"].append(copy.deepcopy(b["models"][0]["draws"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate draw"):
            reconcile(a, b, c)

    def test_full_roster_rejected_when_partial(self):
        with self.assertRaisesRegex(ValueError, "730"):
            reconcile(*fixture(), require_full=True)

    def test_zip_rejects_unexpected_members(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "source.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("../private.txt", "x")
            with self.assertRaisesRegex(ValueError, "unexpected"):
                load_evidence(path)

    def test_zip_rejects_duplicate_members(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "source.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("evidence/p000.json", "{}")
                z.writestr("evidence/p000.json", "{}")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_evidence(path)

    def test_zip_rejects_oversized_member(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "source.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("evidence/p000.json", "x" * (256 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "oversized"):
                load_evidence(path)


if __name__ == "__main__":
    unittest.main()
