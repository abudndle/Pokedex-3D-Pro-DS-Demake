"""C285 synthetic ETC1 5-bit base expansion candidate regressions."""
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c283_private_low_bpp_candidates import etc1_pixel
from c285_private_etc1_quantization import (
    etc1_pixel_floor, floor_matches, quantization_matches)

# Differential red base 20, table1=1, negative modifier 5 on pixel 0.
# Bit replication: 165-5=160 -> 20; integer-floor: 164-5=159 -> 19.
DIFF = (20 << 59) | (1 << 37) | (1 << 33) | (1 << 16)


def fixture(bits, flipped=False):
    blocks = (DIFF, 0, 0, DIFF)
    source = bytearray()
    for block in blocks:
        if bits == 8:
            source.extend(bytes([255]) * 8)
        source.extend(block.to_bytes(8, "little"))
    output = bytearray(struct.pack("<4sHHH", b"P3PX", 2, 8, 8))
    for y in range(8):
        sy = 7 - y if flipped else y
        for x in range(8):
            block = (sy // 4) * 2 + x // 4
            output.extend(struct.pack("<H", etc1_pixel_floor(blocks[block], x % 4, sy % 4)))
    return bytes(source), bytes(output)


class QuantizationTests(unittest.TestCase):
    def test_expansion_is_distinguishable(self):
        self.assertEqual(etc1_pixel(DIFF, 0, 0) & 31, 20)
        self.assertEqual(etc1_pixel_floor(DIFF, 0, 0) & 31, 19)

    def test_both_formats_and_orientations(self):
        for bits in (4, 8):
            for flipped in (True, False):
                with self.subTest(bits=bits, flipped=flipped):
                    source, p3px = fixture(bits, flipped)
                    names = floor_matches(source, 8, 8, p3px, bits)
                    self.assertEqual(len(names), 1)
                    self.assertEqual("FLIP_Y" in names[0] and "NO_FLIP" not in names[0], flipped)
                    self.assertIn(names[0], quantization_matches(source, 8, 8, p3px, bits))

    def test_all_zero_source_remains_ambiguous(self):
        source = bytes(32)
        p3px = struct.pack("<4sHHH", b"P3PX", 2, 8, 8) + struct.pack("<H", 32768) * 64
        self.assertGreater(len(quantization_matches(source, 8, 8, p3px, 4)), 1)

    def test_corrupt_pixel_rejected(self):
        source, p3px = fixture(4)
        self.assertEqual(floor_matches(source, 8, 8, p3px[:-2] + b"\xff\xff", 4), ())

    def test_bad_source_rejected(self):
        source, p3px = fixture(8)
        with self.assertRaisesRegex(ValueError, "source size or tile"):
            floor_matches(source[:-1], 8, 8, p3px, 8)

    def test_bad_p3px_rejected(self):
        source, p3px = fixture(4)
        with self.assertRaisesRegex(ValueError, "P3PX header/dimensions/length"):
            floor_matches(source, 8, 8, p3px[:-2], 4)

    def test_differential_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError, "overflow"):
            etc1_pixel_floor((31 << 59) | (3 << 56) | (1 << 33), 0, 0)


if __name__ == "__main__":
    unittest.main()
