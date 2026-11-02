"""C283 synthetic low-bpp, ETC1/ETC1A4 and private SHA-gate tests."""
import hashlib
import pathlib
import re
import struct
import sys
import tempfile
import types
import unittest
import zipfile
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c283_private_low_bpp_candidates import (
    audit, candidate_matches, compressed_candidate_matches, decode_4,
    decode_8, etc1_pixel, morton8, pack)


def fixture(bits, decode, width=16, height=8, high_first=False):
    source = bytearray(width * height * bits // 8)
    output = bytearray(struct.pack("<4sHHH", b"P3PX", 2, width, height))
    for y in range(height):
        sy = height - 1 - y
        for x in range(width):
            value = (x * 37 + y * 11 + x * y * 3 + 19) & (255 if bits == 8 else 15)
            texel = ((sy // 8) * (width // 8) + x // 8) * 64 + morton8(x % 8, sy % 8)
            if bits == 8:
                source[texel] = value
            else:
                shift = 4 if ((texel % 2 == 0) == high_first) else 0
                source[texel // 2] |= value << shift
            output.extend(struct.pack("<H", decode(value)))
    return bytes(source), bytes(output)


class CandidateTests(unittest.TestCase):
    def test_8bpp_morton_and_all_channel_layouts(self):
        for name in ("L8", "A8", "LA44_L_LOW", "LA44_L_HIGH"):
            with self.subTest(name=name):
                source, p3px = fixture(8, lambda value: decode_8(name, value))
                self.assertIn(name, candidate_matches(source, 16, 8, p3px, 8))

    def test_4bpp_nibble_orders(self):
        for name in ("L4_LOW_FIRST", "L4_HIGH_FIRST", "A4_LOW_FIRST", "A4_HIGH_FIRST"):
            with self.subTest(name=name):
                source, p3px = fixture(4, lambda value: decode_4(name, value),
                                       high_first="HIGH_FIRST" in name)
                self.assertIn(name, candidate_matches(source, 16, 8, p3px, 4))

    def test_etc1_individual_color_and_alpha(self):
        word = (15 << 60) | (15 << 48)
        self.assertEqual(etc1_pixel(word, 0, 0), pack(1, 31, 0, 0))
        self.assertEqual(etc1_pixel(word, 3, 0), pack(1, 0, 31, 0))
        self.assertEqual(etc1_pixel(word, 0, 0, 7), pack(0, 31, 0, 0))

    def test_etc1_differential_horizontal_sign(self):
        word = ((20 << 59) | (6 << 56) | (10 << 51) | (3 << 48) |
                (5 << 43) | (7 << 40) | (1 << 37) | (2 << 34) |
                (1 << 33) | (1 << 32) | (1 << 16))
        self.assertEqual(etc1_pixel(word, 0, 0), pack(1, 20, 9, 4))
        self.assertEqual(etc1_pixel(word, 0, 3), pack(1, 19, 14, 5))

    def test_etc1_and_etc1a4_tiling_and_corruption(self):
        for bits in (4, 8):
            with self.subTest(bits=bits):
                block = b"\x00" * 8 if bits == 4 else b"\xff" * 8 + b"\x00" * 8
                source = block * 8
                p3px = struct.pack("<4sHHH", b"P3PX", 2, 16, 8) + struct.pack("<H", 32768) * 128
                self.assertEqual(len(compressed_candidate_matches(source, 16, 8, p3px, bits)), 1)
                self.assertEqual(compressed_candidate_matches(source, 16, 8, p3px[:-2] + b"\xff\xff", bits), ())

    def test_etc1_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError, "overflow"):
            etc1_pixel((31 << 59) | (3 << 56) | (1 << 33), 0, 0)

    def test_source_dimensions_and_length_fail_closed(self):
        source, p3px = fixture(8, lambda v: decode_8("L8", v))
        for bad, w, h in ((source[:-1], 16, 8), (source, 7, 8),
                          (source, 16, 9), (source, 2048, 8)):
            with self.assertRaisesRegex(ValueError, "source size or tile"):
                candidate_matches(bad, w, h, p3px, 8)
        with self.assertRaisesRegex(ValueError, "source size or tile"):
            candidate_matches(source, 16, 8, p3px, 16)

    def test_p3px_header_version_and_length_fail_closed(self):
        source, p3px = fixture(4, lambda v: decode_4("L4_LOW_FIRST", v))
        for bad in (p3px[:-2], b"BAD!" + p3px[4:], p3px[:4] + b"\x01\x00" + p3px[6:]):
            with self.assertRaisesRegex(ValueError, "P3PX header/dimensions/length"):
                candidate_matches(source, 16, 8, bad, 4)

    def test_uniform_luminance_ambiguity(self):
        source = bytes([255]) * 64
        p3px = struct.pack("<4sHHH", b"P3PX", 2, 8, 8) + struct.pack("<H", 65535) * 64
        self.assertGreater(len(candidate_matches(source, 8, 8, p3px, 8)), 1)


class SyntheticArchiveTests(unittest.TestCase):
    def run_audit(self, bad_sha=False, unexpected=False):
        source, p3px = fixture(8, lambda v: decode_8("L8", v), 8, 8)
        raw = b"synthetic-C5" + source
        offset = len(b"synthetic-C5")
        row = {"byte_density": "8_BPP_STORAGE_ONLY", "source_offset": offset,
               "source_bytes": len(source), "source_sha256": hashlib.sha256(source).hexdigest(),
               "width": 8, "height": 8, "opaque_format": 123}
        cat = {"source_offset": offset,
               "source_sha256": "0" * 64 if bad_sha else row["source_sha256"],
               "width": 8, "height": 8, "opaque_format": 123}
        c275 = types.ModuleType("c275_private_draw_material_chain")
        c275.MEMBER = re.compile(r"decoded_c5/(p\d{3})\.c5\Z")
        c275.ROSTER = {"p000"}
        c275.MAX_ENTRIES = 2048
        c275.MAX_MODEL = 64 * 1024 * 1024
        c275.MAX_TOTAL = 1024 * 1024 * 1024
        c279 = types.ModuleType("c279_private_header_texture_base")
        c279.source_descriptor_metadata = lambda data: [row]
        c278 = types.ModuleType("c278_private_texture_format_evidence")
        c278.parse_catalog = lambda data, mid: [cat]
        c278.MAX_CATALOG = 65536
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for part in (1, 2, 3):
                with zipfile.ZipFile(root / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as z:
                    if part == 1:
                        z.writestr("decoded_c5/p000.c5", raw)
            with zipfile.ZipFile(root / "C84.zip", "w") as z:
                z.writestr("catalogs/p000.p3tm", b"synthetic-catalog-padding")
                z.writestr("textures/p000/t000.p3px", p3px)
                if unexpected:
                    z.writestr("textures/other.png.p3px", b"invalid")
            with patch.dict(sys.modules, {"c275_private_draw_material_chain": c275,
                                          "c279_private_header_texture_base": c279,
                                          "c278_private_texture_format_evidence": c278}):
                return audit(root, root / "C84.zip", require_full=True)

    def test_private_archive_unique_L8(self):
        result = self.run_audit()
        self.assertEqual(result["summary"]["counts"]["unique_candidate_consistent_with_C84"], 1)
        self.assertEqual(result["summary"]["counts"]["candidate_agreement_pixels"], 64)
        self.assertFalse(result["summary"]["independent_gpu_format_verified"])

    def test_private_archive_SHA_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "source SHA/format mismatch"):
            self.run_audit(bad_sha=True)

    def test_private_archive_unexpected_member_rejected(self):
        with self.assertRaisesRegex(ValueError, "unexpected C84"):
            self.run_audit(unexpected=True)


if __name__ == "__main__":
    unittest.main()
