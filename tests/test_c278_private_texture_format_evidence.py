"""C278 synthetic-only P3TM, storage density and source provenance tests."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c278_private_texture_format_evidence import parse_catalog, byte_density


def fixture(model=200, width=4, height=4, count=2):
    body = bytearray()
    for index in range(count):
        name = f"fixture{index}".encode("ascii")
        body += struct.pack("<HHHII32sH", index, width, height, 0x12345678,
                            512 + index * 16, bytes([index + 1]) * 32, len(name)) + name
    return struct.pack("<4sHHHHII", b"P3TM", 1, model, count, 0,
                       len(body), zlib.crc32(body)) + body


class C278Tests(unittest.TestCase):
    def test_exact_catalog(self):
        rows = parse_catalog(fixture(), "p200")
        self.assertEqual([r["index"] for r in rows], [0, 1])
        self.assertEqual(rows[0]["source_name"], "fixture0")
        self.assertEqual(rows[0]["opaque_format"], 0x12345678)

    def test_byte_density_is_not_format(self):
        self.assertEqual(byte_density(8, 4, 4), "4_BPP_STORAGE_ONLY")
        self.assertEqual(byte_density(16, 4, 4), "8_BPP_STORAGE_ONLY")
        self.assertEqual(byte_density(32, 4, 4), "16_BPP_STORAGE_ONLY")
        self.assertEqual(byte_density(64, 4, 4), "32_BPP_STORAGE_ONLY")
        self.assertEqual(byte_density(3, 4, 4), "NONINTEGRAL_OR_PADDED")
        self.assertEqual(byte_density(12, 4, 4), "UNKNOWN_OR_PADDED")

    def test_invalid_density(self):
        for size, width, height in [(0, 4, 4), (1, 0, 1), (-1, 1, 1)]:
            with self.assertRaises(ValueError):
                byte_density(size, width, height)

    def test_corrupt_crc(self):
        broken = bytearray(fixture())
        broken[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            parse_catalog(bytes(broken), "p200")

    def test_wrong_model(self):
        with self.assertRaisesRegex(ValueError, "model"):
            parse_catalog(fixture(), "p201")

    def test_trailing_bytes(self):
        good = fixture()
        body = good[20:] + b"X"
        raw = struct.pack("<4sHHHHII", b"P3TM", 1, 200, 2, 0,
                          len(body), zlib.crc32(body)) + body
        with self.assertRaisesRegex(ValueError, "trailing"):
            parse_catalog(raw, "p200")

    def test_zero_dimension(self):
        broken = bytearray(fixture())
        struct.pack_into("<H", broken, 22, 0)
        struct.pack_into("<I", broken, 16, zlib.crc32(broken[20:]))
        with self.assertRaisesRegex(ValueError, "dimensions"):
            parse_catalog(bytes(broken), "p200")

    def test_non_ascii_name(self):
        broken = bytearray(fixture())
        broken[68] = 1
        struct.pack_into("<I", broken, 16, zlib.crc32(broken[20:]))
        with self.assertRaisesRegex(ValueError, "non-ASCII"):
            parse_catalog(bytes(broken), "p200")

    def test_duplicate_index(self):
        broken = bytearray(fixture())
        second = 20 + 48 + len(b"fixture0")
        struct.pack_into("<H", broken, second, 0)
        struct.pack_into("<I", broken, 16, zlib.crc32(broken[20:]))
        with self.assertRaisesRegex(ValueError, "index"):
            parse_catalog(bytes(broken), "p200")

    def test_truncated_record(self):
        with self.assertRaises(ValueError):
            parse_catalog(fixture()[:25], "p200")


class C278IntegrationTests(unittest.TestCase):
    """Exercise C277/C275 synthetic C5 fixtures in the actual repo."""
    @staticmethod
    def source_fixture():
        from test_c277_private_texture_tail_candidates import synthetic
        return synthetic()

    @staticmethod
    def original_catalog(rows):
        from c275_private_draw_material_chain import c75_from_source
        raw, _ = C278IntegrationTests.source_fixture()
        names = c75_from_source(raw)
        body = bytearray()
        for i, (offset, size, digest) in enumerate(rows):
            name = names[i]["original_texture_name"].encode("ascii")
            body += struct.pack("<HHHII32sH", i, 4, 4, 0x12345678,
                                offset, bytes.fromhex(digest), len(name)) + name
        return struct.pack("<4sHHHHII", b"P3TM", 1, 200, len(rows), 0,
                           len(body), zlib.crc32(body)) + body

    def test_source_sha_anchored_and_unanchored_not_promoted(self):
        from c278_private_texture_format_evidence import verify_model
        raw, rows = self.source_fixture()
        result = verify_model("p200", raw, self.original_catalog(rows), {0: rows[0]})
        self.assertEqual(len(result["records"]), 2)
        self.assertTrue(result["records"][0]["c73_source_sha_anchor"])
        self.assertFalse(result["records"][1]["c73_source_sha_anchor"])
        self.assertFalse(result["records"][0]["pixel_format_decoded"])
        self.assertFalse(result["records"][0]["gpu_sampler_verified"])

    def test_missing_c76_catalog_rows_remain_unverified(self):
        from c278_private_texture_format_evidence import verify_model
        raw, rows = self.source_fixture()
        result = verify_model("p200", raw, self.original_catalog(rows[:1]), {0: rows[0]})
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][1]["byte_density"], "NO_P3TM_METADATA")
        self.assertIsNone(result["records"][1]["opaque_source_format"])
        self.assertFalse(result["records"][1]["c73_source_sha_anchor"])

    def test_anchor_rejects_wrong_p3tm_sha(self):
        from c278_private_texture_format_evidence import verify_model
        raw, rows = self.source_fixture()
        broken = bytearray(self.original_catalog(rows))
        broken[20 + 14] ^= 1
        struct.pack_into("<I", broken, 16, zlib.crc32(broken[20:]))
        with self.assertRaisesRegex(ValueError, "anchor mismatch"):
            verify_model("p200", raw, bytes(broken), {0: rows[0]})

    def test_unanchored_catalog_cannot_promote_source_hash(self):
        from c278_private_texture_format_evidence import verify_model
        raw, rows = self.source_fixture()
        broken = bytearray(self.original_catalog(rows))
        broken[20 + 14] ^= 1
        struct.pack_into("<I", broken, 16, zlib.crc32(broken[20:]))
        result = verify_model("p200", raw, bytes(broken), {})
        self.assertFalse(result["records"][0]["p3tm_sha_matches_tail_candidate"])
        self.assertFalse(result["records"][0]["c73_source_sha_anchor"])

    def test_private_zip_batch_and_full_roster_gate(self):
        from c278_private_texture_format_evidence import audit
        from test_c276_private_source_texture_coverage import archives, catalog
        raw, rows = self.source_fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            archives(root, raw)
            c73 = catalog(root, rows[:1])
            pack = root / "catalogs.zip"
            with zipfile.ZipFile(pack, "w") as z:
                z.writestr("catalogs/p200.p3tm", self.original_catalog(rows))
            result = audit(root, pack, c73)
            self.assertEqual(result["summary"]["models"], 1)
            self.assertEqual(result["summary"]["source_texture_descriptors"], 2)
            self.assertEqual(result["summary"]["c73_sha_anchored_rows"], 1)
            self.assertEqual(result["summary"]["storage_density_classes"], {"8_BPP_STORAGE_ONLY": 2})
            self.assertEqual(result["summary"]["verified_pixel_formats"], 0)
            with self.assertRaisesRegex(ValueError, "730"):
                audit(root, pack, c73, require_full=True)


if __name__ == "__main__":
    unittest.main()
