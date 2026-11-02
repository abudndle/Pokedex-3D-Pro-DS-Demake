"""Synthetic XWD regression tests for independent melonDS window preflight."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c253_melonds_frame_gate import inspect


def make_window(path, width=512, height=768, colored=True):
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[11], header[12] = width, height, 32, width * 4
    pixels = bytearray(width * height * 4)
    if colored:
        for y0, y1 in ((100, 300), (450, 650)):
            for y in range(y0, min(y1, height)):
                for x in range(100, min(300, width)):
                    pixels[(y * width + x) * 4] = 200
    path.write_bytes(struct.pack(">25I", *header) + pixels)


class C253MelonDSFrameTests(unittest.TestCase):
    def test_nonblank_two_halves_is_only_preliminary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "screen.xwd"
            make_window(path)
            result = inspect(path)
            self.assertGreater(result["nonblack_ratio"], 0.05)
            self.assertFalse(result["rom_boot_verified"])
            self.assertFalse(result["dsi_verified"])

    def test_blank_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "screen.xwd"
            make_window(path, colored=False)
            with self.assertRaisesRegex(ValueError, "blank"):
                inspect(path)

    def test_small_or_truncated_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "screen.xwd"
            make_window(path, width=128)
            with self.assertRaisesRegex(ValueError, "geometry"):
                inspect(path)
            path.write_bytes(b"XWD")
            with self.assertRaisesRegex(ValueError, "size"):
                inspect(path)


if __name__ == "__main__":
    unittest.main()
