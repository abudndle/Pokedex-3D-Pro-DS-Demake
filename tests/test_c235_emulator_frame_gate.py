"""Synthetic-only XWD tests for C235 deterministic emulator navigation gate."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c235_emulator_frame_gate import compare_frames, read_xwd


def make_xwd(path, value=0, change=None, width=64, height=64):
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[11], header[12] = width, height, 32, width * 4
    header[19] = 0
    raw = bytearray([value] * (width * height * 4))
    if change:
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                raw[(y * width + x) * 4] = change
    path.write_bytes(struct.pack(">25I", *header) + raw)


class C235FrameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths = [Path(self.temp.name) / f"{n}.xwd"
                      for n in ("home", "dex", "right", "back")]
        for p, val in zip(self.paths, (0, 100, 200, 0)):
            make_xwd(p, val)

    def test_real_transition_and_b_return(self):
        result = compare_frames(*self.paths)
        self.assertGreater(result["dex_right_pixels"], 100)
        self.assertEqual(result["after_b_pixels_different_from_home"], 0)

    def test_ignored_right_fails(self):
        make_xwd(self.paths[2], 100)
        with self.assertRaisesRegex(ValueError, "Right did not"):
            compare_frames(*self.paths)

    def test_ignored_b_fails(self):
        make_xwd(self.paths[3], 200)
        with self.assertRaisesRegex(ValueError, "B did not"):
            compare_frames(*self.paths)

    def test_ignored_a_fails(self):
        make_xwd(self.paths[1], 0)
        with self.assertRaisesRegex(ValueError, "A did not"):
            compare_frames(*self.paths)

    def test_mismatched_geometry_fails(self):
        make_xwd(self.paths[3], 0, width=32)
        with self.assertRaisesRegex(ValueError, "dimensions changed"):
            compare_frames(*self.paths)

    def test_truncated_or_invalid_header_fails(self):
        self.paths[1].write_bytes(b"XWD")
        with self.assertRaisesRegex(ValueError, "invalid XWD file size"):
            compare_frames(*self.paths)
        make_xwd(self.paths[1], 100)
        data = bytearray(self.paths[1].read_bytes())
        struct.pack_into(">I", data, 12, 16)
        self.paths[1].write_bytes(data)
        with self.assertRaisesRegex(ValueError, "invalid XWD image geometry"):
            read_xwd(self.paths[1])

    def test_minimum_threshold_must_be_integer(self):
        with self.assertRaisesRegex(ValueError, "minimum"):
            compare_frames(*self.paths, min_changed=True)


if __name__ == "__main__":
    unittest.main()
