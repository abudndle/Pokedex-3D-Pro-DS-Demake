"""Synthetic C243 DeSmuME menu frame-gate tests, no Nintendo assets."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c243_emulator_menu_gate import verify


def make_xwd(path, value=0, width=256):
    h = [0] * 25
    h[0], h[1], h[2], h[3] = 100, 7, 2, 24
    h[4], h[5], h[11], h[12] = width, 384, 32, width * 4
    path.write_bytes(struct.pack('>25I', *h) + bytes([value, 0, 0, 0]) * (width * 384))


def paint(path, x0, y0, x1, y1, value):
    data = bytearray(path.read_bytes())
    for y in range(y0, y1):
        for x in range(x0, x1):
            data[100 + (y * 256 + x) * 4] = value
    path.write_bytes(data)


class C243MenuGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.frames = [Path(self.temp.name) / f'{s}.xwd' for s in
                       ('home', 'move', 'back', 'ar_selected', 'ar_after_a')]
        for p in self.frames:
            make_xwd(p)
        paint(self.frames[1], 0, 200, 256, 384, 50)
        paint(self.frames[3], 32, 300, 120, 320, 90)
        paint(self.frames[4], 32, 300, 120, 320, 90)

    def test_move_back_and_ar_denial(self):
        r = verify(*self.frames)
        self.assertGreater(r['home_to_move_dex_lower_pixels'], 100)
        self.assertEqual(r['move_dex_b_to_home_lower_pixels'], 0)
        self.assertEqual(r['ar_a_denied_lower_pixels'], 0)

    def test_ignored_move_touch_rejected(self):
        make_xwd(self.frames[1])
        with self.assertRaisesRegex(ValueError, 'Move Dex touch'):
            verify(*self.frames)

    def test_ignored_back_rejected(self):
        make_xwd(self.frames[2], 40)
        with self.assertRaisesRegex(ValueError, 'B did not'):
            verify(*self.frames)

    def test_ignored_ar_selection_rejected(self):
        make_xwd(self.frames[3])
        with self.assertRaisesRegex(ValueError, 'AR Viewer touch'):
            verify(*self.frames)

    def test_ar_page_open_rejected(self):
        paint(self.frames[4], 0, 200, 256, 384, 55)
        with self.assertRaisesRegex(ValueError, 'AR Viewer A'):
            verify(*self.frames)

    def test_top_only_change_does_not_fake_move(self):
        make_xwd(self.frames[1])
        paint(self.frames[1], 0, 0, 256, 192, 50)
        with self.assertRaisesRegex(ValueError, 'Move Dex touch'):
            verify(*self.frames)

    def test_mismatched_window_rejected(self):
        make_xwd(self.frames[4], width=128)
        with self.assertRaisesRegex(ValueError, 'matching 256x384'):
            verify(*self.frames)


if __name__ == '__main__':
    unittest.main()
