"""C287 synthetic source SHA and original draw-to-texture provenance tests."""
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c287_private_draw_texture_chain import join


def fixture():
    c275 = {"summary": {"schema": "C275_PRIVATE_C5_DRAW_MATERIAL_REFERENCE_V1"},
            "models": [{"model_id": "p000", "source_c5_sha256": "b" * 64,
                        "mesh_count": 1, "material_count": 1, "source_texture_count": 2,
                        "draws": [{"draw_index": 0, "mesh_index": 0, "material_index": 0,
                                   "source_texture_reference_indices": [0, 1],
                                   "source_texture_reference_names": ["bodyCl", "bodyNor"]}]}]}
    def desc(i, anchored=True):
        return {"index": i, "source_sha256": "a" * 64, "opaque_format": 7,
                "c73_sha_anchor": anchored, "p3tm_metadata_corrob": anchored}
    c279 = {"summary": {"schema": "C279_PRIVATE_C5_HEADER_TEXTURE_BASE_V1"},
            "models": [{"model_id": "p000", "source_c5_sha256": "b" * 64,
                        "records": [desc(0), desc(1, False)]}]}
    c286 = {"summary": {"schema": "C286_PRIVATE_C5_FORMAT_WORD_CONSENSUS_V1"},
            "textures": [{"model_id": "p000", "texture_index": 0,
                          "source_sha256": "a" * 64, "opaque_source_format": 7,
                          "disposition": "UNIQUE_C84_CONVERSION_CANDIDATE",
                          "format_word_consensus_candidate": "ETC1_FLOOR5_NO_FLIP_Y",
                          "gpu_format_verified": False, "sampler_role_verified": False,
                          "native_p3px_binding_verified": False}]}
    return c275, c279, c286


class DrawTextureChainTests(unittest.TestCase):
    def test_source_draws_join_anchored_and_unanchored_without_sampler_claim(self):
        result = join(*fixture())
        self.assertEqual(result["summary"]["SOURCE_SHA_AND_C84_CANDIDATE"], 1)
        self.assertEqual(result["summary"]["SOURCE_REFERENCE_UNANCHORED"], 1)
        self.assertEqual(result["summary"]["native_p3px_image_bindings_verified"], 0)
        slots = result["models"][0]["draws"][0]["texture_reference_slots"]
        self.assertEqual(slots[0]["candidate_hypothesis"], "ETC1_FLOOR5_NO_FLIP_Y")
        self.assertIsNone(slots[1]["candidate_hypothesis"])

    def test_c275_c279_source_sha_mismatch_rejected(self):
        a, b, c = fixture()
        b["models"][0]["source_c5_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "source SHA mismatch"):
            join(a, b, c)

    def test_candidate_source_sha_mismatch_rejected(self):
        a, b, c = fixture()
        c["textures"][0]["source_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "source SHA/format"):
            join(a, b, c)

    def test_candidate_format_word_mismatch_rejected(self):
        a, b, c = fixture()
        c["textures"][0]["opaque_source_format"] = 8
        with self.assertRaisesRegex(ValueError, "source SHA/format"):
            join(a, b, c)

    def test_forged_gpu_sampler_verification_rejected(self):
        a, b, c = fixture()
        c["textures"][0]["sampler_role_verified"] = True
        with self.assertRaisesRegex(ValueError, "falsely asserts"):
            join(a, b, c)

    def test_bad_material_index_rejected(self):
        a, b, c = fixture()
        a["models"][0]["draws"][0]["material_index"] = 1
        with self.assertRaisesRegex(ValueError, "source material"):
            join(a, b, c)

    def test_bad_texture_reference_rejected(self):
        a, b, c = fixture()
        a["models"][0]["draws"][0]["source_texture_reference_indices"][0] = 2
        with self.assertRaisesRegex(ValueError, "source texture reference"):
            join(a, b, c)

    def test_duplicate_draw_rejected(self):
        a, b, c = fixture()
        a["models"][0]["draws"].append(copy.deepcopy(a["models"][0]["draws"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            join(a, b, c)

    def test_missing_reference_sentinel_is_not_a_sampler(self):
        a, b, c = fixture()
        a["models"][0]["draws"][0]["source_texture_reference_indices"][1] = 65535
        out = join(a, b, c)
        self.assertEqual(out["models"][0]["draws"][0]["texture_reference_slots"][1]["status"],
                         "SOURCE_REFERENCE_ABSENT")

    def test_invalid_name_rejected(self):
        a, b, c = fixture()
        a["models"][0]["draws"][0]["source_texture_reference_names"][0] = ""
        with self.assertRaisesRegex(ValueError, "reference name"):
            join(a, b, c)

    def test_full_roster_requires_730_models(self):
        with self.assertRaisesRegex(ValueError, "730"):
            join(*fixture(), require_full=True)

    def test_missing_source_descriptor_rejected(self):
        a, b, c = fixture()
        b["models"][0]["records"].pop()
        with self.assertRaisesRegex(ValueError, "table bounds"):
            join(a, b, c)


if __name__ == "__main__":
    unittest.main()
