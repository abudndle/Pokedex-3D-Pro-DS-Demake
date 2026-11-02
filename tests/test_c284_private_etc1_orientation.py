"""C284 synthetic vertical orientation and ambiguity regression tests."""
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c283_private_low_bpp_candidates import etc1_pixel
from c284_private_etc1_orientation import orientation_matches


def fixture(bits, flipped=False, uniform=False):
    red = (15 << 60)
    green = (15 << 52)
    blue = (15 << 44)
    black = 0
    blocks = (black,) * 4 if uniform else (red, green, blue, black)
    source = bytearray()
    for word in blocks:
        if bits == 8:
            source.extend(bytes([255]) * 8)
        source.extend(word.to_bytes(8, "little"))
    output = bytearray(struct.pack("<4sHHH", b"P3PX", 2, 8, 8))
    for y in range(8):
        sy = 7 - y if flipped else y
        for x in range(8):
            block = (sy // 4) * 2 + x // 4
            pixel = etc1_pixel(blocks[block], x % 4, sy % 4)
            output.extend(struct.pack("<H", pixel))
    return bytes(source), bytes(output)


class OrientationTests(unittest.TestCase):
    def test_etc1_no_flip_unique(self):
        source, p3px = fixture(4)
        self.assertEqual(orientation_matches(source, 8, 8, p3px, 4), ("ETC1_NO_FLIP_Y",))

    def test_etc1_flip_unique(self):
        source, p3px = fixture(4, flipped=True)
        self.assertEqual(orientation_matches(source, 8, 8, p3px, 4), ("ETC1_FLIP_Y",))

    def test_etc1a4_no_flip_unique(self):
        source, p3px = fixture(8)
        self.assertEqual(orientation_matches(source, 8, 8, p3px, 8), ("ETC1A4_NO_FLIP_Y",))

    def test_etc1a4_flip_unique(self):
        source, p3px = fixture(8, flipped=True)
        self.assertEqual(orientation_matches(source, 8, 8, p3px, 8), ("ETC1A4_FLIP_Y",))

    def test_uniform_source_remains_ambiguous(self):
        source, p3px = fixture(4, uniform=True)
        self.assertEqual(len(orientation_matches(source, 8, 8, p3px, 4)), 2)

    def test_pixel_corruption_does_not_claim_match(self):
        source, p3px = fixture(4)
        broken = p3px[:-2] + b"\xff\xff"
        self.assertEqual(orientation_matches(source, 8, 8, broken, 4), ())

    def test_malformed_source_rejected(self):
        source, p3px = fixture(8)
        with self.assertRaisesRegex(ValueError, "source size or tile"):
            orientation_matches(source[:-1], 8, 8, p3px, 8)

    def test_invalid_p3px_rejected(self):
        source, p3px = fixture(4)
        with self.assertRaisesRegex(ValueError, "P3PX header/dimensions/length"):
            orientation_matches(source, 8, 8, p3px[:-2], 4)


if __name__ == "__main__":
    unittest.main()
