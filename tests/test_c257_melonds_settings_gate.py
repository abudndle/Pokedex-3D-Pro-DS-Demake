"""C257 synthetic Settings entry, A rotation and B return regressions."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c257_melonds_settings_gate import verify_settings
from test_c254_melonds_nav_gate import make, WIDTH


def patch(path, box, value):
    data = bytearray(path.read_bytes())
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            at = 100 + (y * WIDTH + x) * 4
            data[at:at+4] = bytes((value, value, value, 255))
    path.write_bytes(data)


class C257SettingsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.paths = [Path(tmp.name) / f'{n}.xwd' for n in ('scrolled', 'settings', 'toggled', 'back')]
        for p, variant in zip(self.paths, ('home', 'dex', 'dex', 'home')):
            make(p, variant)
        patch(self.paths[2], (102, 315, 145, 325), 215)

    def test_settings_toggle_and_return(self):
        result = verify_settings(*self.paths)
        self.assertGreater(result['rotation_value_changed_pixels'], 8)
        self.assertFalse(result['save_persistence_verified'])

    def test_settings_not_open(self):
        make(self.paths[1], 'home')
        with self.assertRaisesRegex(ValueError, 'Settings did not open'):
            verify_settings(*self.paths)

    def test_rotation_not_toggled(self):
        self.paths[2].write_bytes(self.paths[1].read_bytes())
        with self.assertRaisesRegex(ValueError, 'rotation toggle'):
            verify_settings(*self.paths)

    def test_unexpected_header_change(self):
        patch(self.paths[2], (20, 224, 180, 250), 240)
        with self.assertRaisesRegex(ValueError, 'rotation toggle'):
            verify_settings(*self.paths)

    def test_b_does_not_return_home(self):
        make(self.paths[3], 'dex')
        with self.assertRaisesRegex(ValueError, 'B did not restore'):
            verify_settings(*self.paths)

    def test_wrong_window_geometry(self):
        import struct
        p = self.paths[3]
        data = bytearray(p.read_bytes())
        struct.pack_into('>I', data, 4 * 4, 255)
        p.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'geometry'):
            verify_settings(*self.paths)


if __name__ == '__main__':
    unittest.main()
