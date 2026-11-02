"""C280 synthetic 8x8 Morton/vertical-flip source to P3PX differential."""
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c280_private_rgba8_pixel_equivalence import convert_candidate, compare_candidate, morton8

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
    source = bytearray(width * height * 4)
    expected = bytearray(struct.pack("<4sHHH", b"P3PX", 2, width, height))
    for y in range(height):
        for x in range(width):
            a = 127 if x % 8 < 4 else 128
            r = (x * 19 + 7) % 256
            g = (y * 23 + 11) % 256
            b = (x * 5 + y * 9) % 256
            sy = height - 1 - y
            source_index = ((sy // 8) * (width // 8) + x // 8) * 64 + MORTON[sy % 8][x % 8]
            source[source_index * 4:source_index * 4 + 4] = bytes((a, r, g, b))
            pixel = ((a >= 128) << 15) | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)
            expected += struct.pack("<H", pixel)
    return bytes(source), bytes(expected)


class C280Tests(unittest.TestCase):
    def test_morton_reference_coordinates(self):
        for y in range(8):
            for x in range(8):
                self.assertEqual(morton8(x, y), MORTON[y][x])

    def test_exact_8x8_rgb_alpha_and_vertical_flip(self):
        source, expected = fixture()
        self.assertEqual(convert_candidate(source, 8, 8), expected)
        self.assertEqual(compare_candidate(source, 8, 8, expected), 64)

    def test_exact_two_tile_source(self):
        source, expected = fixture(16, 8)
        self.assertEqual(convert_candidate(source, 16, 8), expected)

    def test_alpha_threshold_127_vs_128(self):
        source, expected = fixture()
        pixels = struct.unpack_from("<64H", expected, 10)
        self.assertTrue(all((pixels[y * 8 + x] >> 15) == (x >= 4)
                            for y in range(8) for x in range(8)))

    def test_corrupted_pixel_rejected(self):
        source, expected = fixture()
        broken = bytearray(expected)
        broken[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "pixel mismatch"):
            compare_candidate(source, 8, 8, bytes(broken))

    def test_invalid_source_size_or_tiles_rejected(self):
        source, expected = fixture()
        for bad, w, h in [(source[:-1], 8, 8), (source, 7, 8), (source, 8, 9)]:
            with self.assertRaisesRegex(ValueError, "size or tile"):
                convert_candidate(bad, w, h)

    def test_invalid_p3px_header_and_dimensions_rejected(self):
        source, expected = fixture()
        for bad in (b"bad", expected[:8] + b"\x00\x00" + expected[10:], expected[:-2]):
            with self.assertRaisesRegex(ValueError, "header/dimensions/length"):
                compare_candidate(source, 8, 8, bad)


if __name__ == "__main__":
    unittest.main()
