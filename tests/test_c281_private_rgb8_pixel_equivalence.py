"""C281 synthetic 24-bpp source RGB Morton/flip to opaque A1RGB555."""
import pathlib
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c281_private_rgb8_pixel_equivalence import convert_rgb8_candidate, compare_rgb8_candidate

MORTON = (
    (0, 1, 4, 5, 16, 17, 20, 21),
    (2, 3, 6, 7, 18, 19, 22, 23),
    (8, 9, 12, 13, 24, 25, 28, 29),
    (10, 11, 14, 15, 26, 27, 30, 31),
    (32, 33, 36, 37, 48, 49, 52, 53),
    (34, 35, 38, 39, 50, 51, 54, 55),
    (40, 41, 44, 45, 56, 57, 60, 61),
    (42, 43, 46, 47, 58, 59, 62, 63),
)


def fixture(width=8, height=8):
    source = bytearray(width * height * 3)
    expected = bytearray(struct.pack("<4sHHH", b"P3PX", 2, width, height))
    for y in range(height):
        for x in range(width):
            red = (x * 19 + 7) % 256
            green = (y * 23 + 11) % 256
            blue = (x * 5 + y * 9) % 256
            sy = height - 1 - y
            idx = ((sy // 8) * (width // 8) + x // 8) * 64 + MORTON[sy % 8][x % 8]
            source[idx * 3:idx * 3 + 3] = bytes((red, green, blue))
            expected += struct.pack("<H", 0x8000 | ((blue >> 3) << 10) |
                                    ((green >> 3) << 5) | (red >> 3))
    return bytes(source), bytes(expected)


class C281Tests(unittest.TestCase):
    def test_exact_8x8_and_opaque_alpha(self):
        source, expected = fixture()
        self.assertEqual(convert_rgb8_candidate(source, 8, 8), expected)
        self.assertEqual(compare_rgb8_candidate(source, 8, 8, expected), 64)
        self.assertTrue(all(pixel & 0x8000 for pixel in struct.unpack_from("<64H", expected, 10)))

    def test_two_tiles(self):
        source, expected = fixture(16, 8)
        self.assertEqual(convert_rgb8_candidate(source, 16, 8), expected)

    def test_stdlib_fallback(self):
        source, expected = fixture(16, 8)
        with patch.dict(sys.modules, {"numpy": None}):
            self.assertEqual(convert_rgb8_candidate(source, 16, 8), expected)

    def test_source_length_and_dimensions_rejected(self):
        source, expected = fixture()
        for bad, w, h in ((source[:-1], 8, 8), (source, 7, 8), (source, 8, 9)):
            with self.assertRaisesRegex(ValueError, "size or tile"):
                convert_rgb8_candidate(bad, w, h)

    def test_p3px_pixel_corruption_rejected(self):
        source, expected = fixture()
        broken = bytearray(expected)
        broken[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "pixel mismatch"):
            compare_rgb8_candidate(source, 8, 8, bytes(broken))

    def test_p3px_header_and_length_rejected(self):
        source, expected = fixture()
        for bad in (b"bad", expected[:-2], expected[:8] + b"\x00\x00" + expected[10:]):
            with self.assertRaisesRegex(ValueError, "header/dimensions/length"):
                compare_rgb8_candidate(source, 8, 8, bad)


if __name__ == "__main__":
    unittest.main()
