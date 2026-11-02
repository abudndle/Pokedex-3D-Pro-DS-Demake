"""C286 source-format consensus tests contain synthetic metadata only."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c286_private_format_consensus import reconcile, _read_private_json


def fixtures():
    def source(index, fmt=7, bits=4):
        return {"index": index, "opaque_format": fmt, "source_sha256": "a" * 64,
                "c73_sha_anchor": True, "p3tm_metadata_corrob": True,
                "byte_density": f"{bits}_BPP_STORAGE_ONLY"}
    c279 = {"summary": {"schema": "C279_PRIVATE_C5_HEADER_TEXTURE_BASE_V1"},
            "models": [{"model_id": "p000", "records": [source(0), source(1)]},
                       {"model_id": "p001", "records": [source(0, 8, 8)]}]}
    def candidate(mid, idx, bits, names):
        return {"model_id": mid, "texture_index": idx, "storage_bits_per_pixel": bits,
                "status": ("no_supported_candidate_not_verified" if not names else
                           "unique_candidate_consistent_with_C84" if len(names) == 1 else
                           "ambiguous_candidates_not_verified"), "candidates": names}
    c285 = {"summary": {"schema": "C285_PRIVATE_ETC1_5BIT_EXPANSION_CANDIDATES_V1", "models": 2},
            "textures": [candidate("p000", 0, 4, ["ETC1_FLOOR5_NO_FLIP_Y"]),
                         candidate("p000", 1, 4, ["ETC1_FLOOR5_NO_FLIP_Y", "ETC1_LE_3DS_TILE"]),
                         candidate("p001", 0, 8, ["L8", "ETC1A4_FLOOR5_NO_FLIP_Y"])]}
    return c279, c285


class FormatConsensusTests(unittest.TestCase):
    def test_unique_anchor_narrows_ambiguous_without_gpu_proof(self):
        out = reconcile(*fixtures())
        self.assertEqual(out["summary"]["ambiguous_narrowed_by_repeated_source_word"], 1)
        self.assertEqual(out["summary"]["remaining_ambiguous_C84_candidates"], 1)
        self.assertFalse(out["summary"]["independent_gpu_format_verified"])
        self.assertFalse(out["summary"]["native_material_sampler_binding_verified"])
        self.assertEqual(out["textures"][1]["format_word_consensus_candidate"], "ETC1_FLOOR5_NO_FLIP_Y")

    def test_conflicting_unique_anchors_fail_closed(self):
        a, b = fixtures()
        b["textures"][1]["candidates"] = ["ETC1_LE_3DS_TILE"]
        b["textures"][1]["status"] = "unique_candidate_consistent_with_C84"
        out = reconcile(a, b)
        self.assertEqual(out["summary"]["conflicting_source_format_words"], 1)
        self.assertIsNone(out["textures"][0]["format_word_consensus_candidate"])
        self.assertEqual(out["textures"][1]["disposition"], "CONFLICTING_SOURCE_FORMAT_WORD")

    def test_only_ambiguous_group_remains_ambiguous(self):
        a, b = fixtures()
        b["textures"][0]["candidates"].append("ETC1_LE_3DS_TILE")
        b["textures"][0]["status"] = "ambiguous_candidates_not_verified"
        out = reconcile(a, b)
        self.assertEqual(out["summary"]["remaining_ambiguous_C84_candidates"], 3)
        self.assertNotIn("ambiguous_narrowed_by_repeated_source_word", out["summary"])

    def test_duplicate_candidate_row_rejected(self):
        a, b = fixtures()
        b["textures"].append(copy.deepcopy(b["textures"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reconcile(a, b)

    def test_duplicate_source_model_rejected(self):
        a, b = fixtures()
        a["models"].append(copy.deepcopy(a["models"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reconcile(a, b)

    def test_unanchored_source_rejected(self):
        a, b = fixtures()
        a["models"][0]["records"][0]["c73_sha_anchor"] = False
        with self.assertRaisesRegex(ValueError, "not independently anchored"):
            reconcile(a, b)

    def test_density_disagreement_rejected(self):
        a, b = fixtures()
        a["models"][0]["records"][0]["byte_density"] = "8_BPP_STORAGE_ONLY"
        with self.assertRaisesRegex(ValueError, "not independently anchored"):
            reconcile(a, b)

    def test_status_mismatch_rejected(self):
        a, b = fixtures()
        b["textures"][0]["status"] = "ambiguous_candidates_not_verified"
        with self.assertRaisesRegex(ValueError, "contradicts"):
            reconcile(a, b)

    def test_wrong_bit_candidate_rejected(self):
        a, b = fixtures()
        b["textures"][0]["candidates"] = ["ETC1A4_FLOOR5_NO_FLIP_Y"]
        with self.assertRaisesRegex(ValueError, "invalid or duplicate"):
            reconcile(a, b)

    def test_invalid_sha_rejected(self):
        a, b = fixtures()
        a["models"][0]["records"][0]["source_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "source provenance"):
            reconcile(a, b)

    def test_require_full_rejects_partial_roster(self):
        with self.assertRaisesRegex(ValueError, "full 730"):
            reconcile(*fixtures(), require_full=True)

    def test_private_json_symlink_and_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            source = root / "private.json"
            source.write_text(json.dumps({"safe": True}))
            self.assertEqual(_read_private_json(source), {"safe": True})
            link = root / "link.json"
            link.symlink_to(source)
            with self.assertRaises(OSError):
                _read_private_json(link)
            link.unlink()
            link.hardlink_to(source)
            with self.assertRaisesRegex(ValueError, "single-link"):
                _read_private_json(source)


if __name__ == "__main__":
    unittest.main()
