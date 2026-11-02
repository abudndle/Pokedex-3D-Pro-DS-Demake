"""C254 fail-closed melonDS dual-screen navigation synthetic regressions."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c254_melonds_nav_gate import verify_navigation

WIDTH, HEIGHT = 256, 403


def make(path, variant):
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[11], header[12] = WIDTH, HEIGHT, 32, WIDTH * 4
    buf = bytearray(WIDTH * HEIGHT * 4)
    def paint(box, value):
        x0, y0, x1, y1 = box
        for y in range(y0, y1):
            for x in range(x0, x1):
                at = (y * WIDTH + x) * 4
                buf[at:at + 4] = bytes((value, value, value, 255))
    paint((0, 19, 256, 210), 40)
    paint((0, 211, 256, 403), 20)
    paint((20, 80, 120, 160), 130)
    paint((20, 280, 120, 370), 130)
    if variant in ('dex', 'right', 'broken_b'):
        paint((0, 44, 256, 100), 75)
        paint((0, 300, 256, 380), 75)
    if variant in ('right', 'broken_b'):
        paint((117, 56, 146, 71), 220)
        paint((68, 311, 100, 331), 220)
    path.write_bytes(struct.pack('>25I', *header) + buf)


class C254NavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = [Path(self.tmp.name) / (n + '.xwd') for n in ('home', 'dex', 'right', 'back')]
        for path, variant in zip(self.paths, ('home', 'dex', 'right', 'home')):
            make(path, variant)

    def test_two_number_changes_and_home_restored(self):
        result = verify_navigation(*self.paths)
        self.assertGreater(result['right_top_number_pixels'], 6)
        self.assertGreater(result['right_bottom_number_pixels'], 6)
        self.assertFalse(result['dsi_camera_verified'])

    def test_unmapped_right_rejected(self):
        make(self.paths[2], 'dex')
        with self.assertRaisesRegex(ValueError, 'Right did not'):
            verify_navigation(*self.paths)

    def test_only_upper_number_changed_rejected(self):
        data = bytearray(self.paths[2].read_bytes())
        baseline = self.paths[1].read_bytes()
        for y in range(311, 331):
            off = 100 + y * WIDTH * 4 + 68 * 4
            data[off:off + 32 * 4] = baseline[off:off + 32 * 4]
        self.paths[2].write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'BOTH'):
            verify_navigation(*self.paths)

    def test_unmapped_b_rejected(self):
        make(self.paths[3], 'broken_b')
        with self.assertRaisesRegex(ValueError, 'B did not'):
            verify_navigation(*self.paths)

    def test_wrong_window_shape_rejected(self):
        data = self.paths[3].read_bytes()
        hdr = list(struct.unpack_from('>25I', data))
        hdr[4] = 255
        self.paths[3].write_bytes(struct.pack('>25I', *hdr) + data[100:])
        with self.assertRaisesRegex(ValueError, 'geometry'):
            verify_navigation(*self.paths)


if __name__ == '__main__':
    unittest.main()
