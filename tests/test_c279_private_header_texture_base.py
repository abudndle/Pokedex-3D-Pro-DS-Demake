"""C279 synthetic C5 header texture-base and independent C73 SHA gates."""
import csv
import hashlib
import pathlib
import stat
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c279_private_header_texture_base import source_ranges, verify_model, audit
from c275_private_draw_material_chain import write_private_report


def fixture():
    raw = bytearray(552)
    raw[:2] = b"\xc5x"
    struct.pack_into("<H", raw, 0x0e, 2)
    struct.pack_into("<I", raw, 0x04, 400)  # 400 + 0x78 = payload at 520
    struct.pack_into("<II", raw, 0x30, 136, 192)
    struct.pack_into("<I", raw, 0x64, 400)
    for i, (offset, size, nameptr) in enumerate(((0, 16, 70), (16, 16, 77))):
        struct.pack_into("<I", raw, 136 + i * 28, offset)
        struct.pack_into("<I", raw, 136 + i * 28 + 8, nameptr)
        struct.pack_into("<I", raw, 136 + i * 28 + 12, size)
        struct.pack_into("<HHI", raw, 136 + i * 28 + 16, 4, 4, 0x12345678)
    raw[470:477] = b"bodyCl\0"
    raw[477:487] = b"bodyNorOS\0"
    raw[520:552] = bytes(range(32))
    data = bytes(raw)
    rows = [(520 + i * 16, 16, hashlib.sha256(data[520 + i * 16:536 + i * 16]).hexdigest())
            for i in range(2)]
    return data, rows


def p3tm_fixture(rows):
    body = bytearray()
    for i, (offset, size, digest) in enumerate(rows):
        name = (b"bodyCl", b"bodyNorOS")[i]
        body += struct.pack("<HHHII32sH", i, 4, 4, 0x12345678,
                            offset, bytes.fromhex(digest), len(name)) + name
    return struct.pack("<4sHHHHII", b"P3TM", 1, 200, len(rows), 0,
                       len(body), zlib.crc32(body)) + body


class C279Tests(unittest.TestCase):
    def test_header_base_independent_source_sha(self):
        raw, rows = fixture()
        self.assertEqual(source_ranges(raw), rows)
        result = verify_model("p200", raw, dict(enumerate(rows)))
        self.assertEqual([x["status"] for x in result["records"]], ["C73_SOURCE_SHA_VERIFIED"] * 2)

    def test_missing_catalog_rows_are_not_promoted(self):
        raw, rows = fixture()
        result = verify_model("p200", raw, {0: rows[0]})
        self.assertEqual(result["records"][1]["status"], "HEADER_BASE_CANDIDATE_NOT_IN_C73")

    def test_wrong_header_base_rejected(self):
        raw, rows = fixture()
        broken = bytearray(raw)
        struct.pack_into("<I", broken, 4, 500)
        with self.assertRaisesRegex(ValueError, "outside source"):
            source_ranges(bytes(broken))

    def test_wrong_header_base_within_file_fails_sha(self):
        raw, rows = fixture()
        broken = bytearray(raw)
        struct.pack_into("<I", broken, 4, 392)
        with self.assertRaisesRegex(ValueError, "disagrees"):
            verify_model("p200", bytes(broken), {0: rows[0]})

    def test_bad_relative_offset_rejected(self):
        raw, _ = fixture()
        broken = bytearray(raw)
        struct.pack_into("<I", broken, 136 + 28, 15)
        with self.assertRaisesRegex(ValueError, "not contiguous"):
            source_ranges(bytes(broken))

    def test_bad_source_hash_rejected(self):
        raw, rows = fixture()
        with self.assertRaisesRegex(ValueError, "disagrees"):
            verify_model("p200", raw, {0: (rows[0][0], rows[0][1], "0" * 64)})

    def test_original_source_descriptor_metadata_matches_p3tm(self):
        raw, rows = fixture()
        result = verify_model("p200", raw, dict(enumerate(rows)), p3tm_fixture(rows))
        self.assertEqual(sum(x["p3tm_metadata_corrob"] for x in result["records"]), 2)
        self.assertEqual([x["byte_density"] for x in result["records"]], ["8_BPP_STORAGE_ONLY"] * 2)

    def test_p3tm_dimension_mismatch_rejected(self):
        raw, rows = fixture()
        broken = bytearray(p3tm_fixture(rows))
        struct.pack_into("<H", broken, 22, 8)
        struct.pack_into("<I", broken, 16, zlib.crc32(broken[20:]))
        with self.assertRaisesRegex(ValueError, "dimensions or format"):
            verify_model("p200", raw, dict(enumerate(rows)), bytes(broken))

    def test_private_archive_and_full_roster_gate(self):
        raw, rows = fixture()
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            for part in (1, 2, 3):
                with zipfile.ZipFile(folder / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as z:
                    if part == 1:
                        z.writestr("decoded_c5/p200.c5", raw)
            csvpath = folder / "c73.csv"
            with csvpath.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["model_id", "index", "source_offset",
                                                   "source_bytes", "sha256", "provenance"])
                w.writeheader()
                w.writerow(dict(model_id="p200", index=0, source_offset=rows[0][0],
                                source_bytes=rows[0][1], sha256=rows[0][2], provenance="C5_byte_exact"))
            result = audit(folder, csvpath)
            self.assertEqual(result["summary"]["source_sha_anchored"], 1)
            self.assertEqual(result["summary"]["header_base_only_unanchored"], 1)
            self.assertFalse(result["summary"]["release_ready"])
            report = folder / "private.json"
            write_private_report(report, result)
            self.assertEqual(stat.S_IMODE(report.stat().st_mode), 0o600)
            with self.assertRaisesRegex(ValueError, "730"):
                audit(folder, csvpath, require_full=True)


if __name__ == "__main__":
    unittest.main()
