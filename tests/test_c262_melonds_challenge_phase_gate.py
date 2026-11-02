"""C262 fail-closed synthetic dual-screen Challenge phase regressions."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c262_melonds_challenge_phase_gate import verify_phases


def make_frame(path, stage=0, top_only=False, width=256):
    height = 403
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[11], header[12] = width, height, 32, width * 4
    pixels = bytearray(width * height * 4)
    for y in range(55, 160):
        for x in range(35, 180):
            pixels[(y*width+x)*4] = 150
    for y in range(280, 365):
        for x in range(35, 180):
            pixels[(y*width+x)*4] = 150
    # Each phase changes a distinct rectangle in the lower screen.
    if stage:
        for y in range(295, 320):
            for x in range(50, 95):
                pixels[(y*width+x)*4] = 150 if top_only else (25+stage*40)
        if top_only:
            for y in range(70, 105):
                for x in range(50, 95):
                    pixels[(y*width+x)*4] = 25+stage*40
    path.write_bytes(struct.pack('>25I', *header)+pixels)


class C262PhaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = [Path(self.tmp.name)/f'{i}.xwd' for i in range(3)]
        for i, path in enumerate(self.paths):
            make_frame(path, i)

    def test_real_distinct_lower_phases(self):
        result = verify_phases(*self.paths)
        self.assertGreater(result['question_to_review']['lower_samples'], 12)
        self.assertFalse(result['original_assets_verified'])

    def test_unchanged_review_rejected(self):
        self.paths[1].write_bytes(self.paths[0].read_bytes())
        with self.assertRaisesRegex(ValueError, 'question_to_review'):
            verify_phases(*self.paths)

    def test_unchanged_continue_rejected(self):
        self.paths[2].write_bytes(self.paths[1].read_bytes())
        with self.assertRaisesRegex(ValueError, 'review_to_continue'):
            verify_phases(*self.paths)

    def test_top_only_false_positive_rejected(self):
        make_frame(self.paths[1], 1, top_only=True)
        with self.assertRaisesRegex(ValueError, 'lower DS'):
            verify_phases(*self.paths)

    def test_geometry_mismatch_rejected(self):
        make_frame(self.paths[2], 2, width=280)
        with self.assertRaisesRegex(ValueError, 'geometry changed'):
            verify_phases(*self.paths)

    def test_blank_frame_rejected(self):
        self.paths[2].write_bytes(b'')
        with self.assertRaises(ValueError):
            verify_phases(*self.paths)


if __name__ == '__main__':
    unittest.main()
