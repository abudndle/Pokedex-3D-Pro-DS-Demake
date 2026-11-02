"""Synthetic XWD regressions for C268's real melonDS Album acceptance gate."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c268_melonds_album_frame_gate import verify_album

WIDTH, HEIGHT = 256, 403


def make(path, stage):
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[11], header[12] = WIDTH, HEIGHT, 32, WIDTH * 4
    pixels = bytearray(WIDTH * HEIGHT * 4)

    def paint(box, value):
        x0, y0, x1, y1 = box
        for y in range(y0, y1):
            for x in range(x0, x1):
                offset = (y * WIDTH + x) * 4
                pixels[offset:offset + 4] = bytes((value, value, value, 255))

    paint((0, 19, 256, 210), 40)
    paint((0, 211, 256, 403), 20)
    paint((20, 80, 120, 160), 130)
    paint((20, 290, 120, 370), 130)
    if stage != 'home':
        paint((0, 44, 256, 100), 75)
        paint((0, 290, 256, 380), 75)
        paint((20, 120, 150, 158), 110)
        paint((20, 310, 150, 360), 110)
    if stage == 'second':
        paint((20, 120, 150, 158), 180)
        paint((20, 310, 150, 360), 180)
    if stage == 'confirm':
        paint((20, 160, 160, 175), 180)
    if stage in ('deleted', 'resumed'):
        paint((20, 120, 150, 158), 160)
        paint((20, 310, 150, 360), 160)
    path.write_bytes(struct.pack('>25I', *header) + pixels)


class C268AlbumFrameTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        stages = ('home', 'first', 'second', 'first', 'confirm', 'deleted', 'resumed')
        self.paths = [Path(temp.name) / f'{i}.xwd' for i in range(len(stages))]
        for path, stage in zip(self.paths, stages):
            make(path, stage)

    def test_album_lifecycle(self):
        result = verify_album(*self.paths)
        self.assertGreater(result['page_right_top'], 10)
        self.assertFalse(result['dsi_camera_verified'])

    def test_album_did_not_open(self):
        make(self.paths[1], 'home')
        with self.assertRaisesRegex(ValueError, 'did not open'):
            verify_album(*self.paths)

    def test_right_did_not_page(self):
        make(self.paths[2], 'first')
        with self.assertRaisesRegex(ValueError, 'Right did not'):
            verify_album(*self.paths)

    def test_left_did_not_return(self):
        make(self.paths[3], 'second')
        with self.assertRaisesRegex(ValueError, 'Left did not'):
            verify_album(*self.paths)

    def test_x_did_not_confirm(self):
        make(self.paths[4], 'first')
        with self.assertRaisesRegex(ValueError, 'delete confirmation'):
            verify_album(*self.paths)

    def test_a_did_not_delete(self):
        make(self.paths[5], 'confirm')
        with self.assertRaisesRegex(ValueError, 'A did not'):
            verify_album(*self.paths)

    def test_deletion_not_persistent(self):
        make(self.paths[6], 'first')
        with self.assertRaisesRegex(ValueError, 'persist'):
            verify_album(*self.paths)

    def test_geometry_mismatch(self):
        p = self.paths[6]
        data = bytearray(p.read_bytes())
        struct.pack_into('>I', data, 4 * 4, 255)
        p.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'geometry'):
            verify_album(*self.paths)


if __name__ == '__main__':
    unittest.main()
