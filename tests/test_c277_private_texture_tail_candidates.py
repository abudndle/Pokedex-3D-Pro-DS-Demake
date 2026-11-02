"""C277 synthetic-only original-C5 texture-tail hypothesis regressions."""
import hashlib
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from c277_private_texture_tail_candidates import candidates, verify_model, audit
from c275_private_draw_material_chain import write_private_report
from test_c275_private_draw_material_chain import fixture
from test_c276_private_source_texture_coverage import catalog, archives


def synthetic():
    original, _ = fixture()
    data = bytearray(original)
    table = struct.unpack_from("<I", data, 0x30)[0]
    for i, (offset, size) in enumerate(((0, 16), (16, 16))):
        struct.pack_into("<I", data, table + i * 28, offset)
        struct.pack_into("<I", data, table + i * 28 + 12, size)
    base = len(data)
    data.extend(bytes(range(32)))
    raw = bytes(data)
    rows = [(base + i * 16, 16, hashlib.sha256(raw[base + i * 16:base + (i + 1) * 16]).hexdigest())
            for i in range(2)]
    return raw, rows


class C277Tests(unittest.TestCase):
    def test_strict_contiguous_tail_ranges(self):
        raw, rows = synthetic()
        self.assertEqual(candidates(raw), rows)

    def test_c73_source_range_and_sha_corrob(self):
        raw, rows = synthetic()
        result = verify_model("p200", raw, dict(enumerate(rows)))
        self.assertEqual(result["c73_corrob_source_ranges"], 2)
        self.assertEqual(result["candidate_missing_rows"], [])
        self.assertEqual(result["verified_missing_source_payload_bases"], 0)

    def test_unanchored_missing_is_not_verified(self):
        raw, rows = synthetic()
        result = verify_model("p200", raw, {})
        self.assertFalse(result["c73_independent_model_anchor"])
        self.assertEqual(len(result["candidate_missing_rows"]), 2)
        self.assertEqual(result["candidate_missing_rows"][0]["candidate_source_offset"], rows[0][0])
        self.assertEqual(result["candidate_missing_rows"][0]["status"], "UNVERIFIED_EOF_TAIL_HYPOTHESIS")

    def test_reject_c73_wrong_offset_even_when_sha_matches(self):
        raw, rows = synthetic()
        wrong = (rows[0][0] - 1, rows[0][1], rows[0][2])
        with self.assertRaisesRegex(ValueError, "range/SHA"):
            verify_model("p200", raw, {0: wrong})

    def test_reject_c73_wrong_size_and_hash(self):
        raw, rows = synthetic()
        for wrong in ((rows[0][0], 15, rows[0][2]), (rows[0][0], 16, "0" * 64)):
            with self.assertRaisesRegex(ValueError, "range/SHA"):
                verify_model("p200", raw, {0: wrong})

    def test_reject_descriptor_gap_and_overlap(self):
        raw, _ = synthetic()
        table = struct.unpack_from("<I", raw, 0x30)[0]
        for second in (15, 17):
            broken = bytearray(raw)
            struct.pack_into("<I", broken, table + 28, second)
            with self.assertRaisesRegex(ValueError, "not contiguous"):
                candidates(bytes(broken))

    def test_reject_zero_and_out_of_bounds_descriptor(self):
        raw, _ = synthetic()
        table = struct.unpack_from("<I", raw, 0x30)[0]
        for size in (0, 0xffffffff):
            broken = bytearray(raw)
            struct.pack_into("<I", broken, table + 12, size)
            with self.assertRaises(ValueError):
                candidates(bytes(broken))

    def test_reject_wrong_roster_and_bad_header(self):
        raw, _ = synthetic()
        with self.assertRaisesRegex(ValueError, "roster"):
            verify_model("p721", raw, {})
        with self.assertRaisesRegex(ValueError, "size"):
            candidates(b"bad")

    def test_bounded_batch_and_full_roster(self):
        raw, rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            archives(folder, raw)
            c73 = catalog(folder, rows[:1])
            result = audit(folder, c73)
            summary = result["summary"]
            self.assertEqual(summary["c73_corrob_source_ranges"], 1)
            self.assertEqual(summary["missing_eof_tail_candidates"], 1)
            self.assertEqual(summary["verified_missing_original_pixel_bases"], 0)
            self.assertFalse(summary["release_ready"])
            with self.assertRaisesRegex(ValueError, "730"):
                audit(folder, c73, require_full=True)
            private = folder / "private.json"
            write_private_report(private, result)
            self.assertEqual(private.stat().st_mode & 0o777, 0o600)

    def test_duplicate_model_fail_closed(self):
        raw, rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            archives(folder, raw)
            c73 = catalog(folder, rows)
            with zipfile.ZipFile(folder / "Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip", "a") as z:
                z.writestr("decoded_c5/p200.c5", raw)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                audit(folder, c73)

    def test_corrupted_source_texture_cannot_match_anchor(self):
        raw, rows = synthetic()
        broken = bytearray(raw)
        broken[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "range/SHA"):
            verify_model("p200", bytes(broken), dict(enumerate(rows)))


if __name__ == "__main__":
    unittest.main()
