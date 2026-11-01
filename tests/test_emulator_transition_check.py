import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'emulator_transition_check.py'
spec = importlib.util.spec_from_file_location('c148', SCRIPT)
c148 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c148)


def make_xwd(path, rows):
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[7] = 256, 384, 0
    header[11], header[12], header[19] = 32, 1024, 0
    raw = bytearray(struct.pack('>25I', *header))
    for row in rows:
        for x in range(256):
            raw += row[x * 3:x * 3 + 3] + b'\0'
    path.write_bytes(raw)


def rows(base=0):
    return [bytes([base, base, base]) * 256 for _ in range(384)]


class EmulatorFrameTests(unittest.TestCase):
    def test_successful_transition_and_browse(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / f'{i}.xwd' for i in range(4)]
            home = rows(0)
            dex = rows(0)
            dex[100:120] = rows(80)[100:120]
            dex[240:280] = rows(80)[240:280]
            browsed = list(dex)
            browsed[280] = bytes([180, 180, 180]) * 256
            for path, data in zip(paths, (home, dex, browsed, home)):
                make_xwd(path, data)
            report = c148.verify(*paths)
            self.assertGreater(report['dex_lower_screen_changed_pixels'], 0)

    def test_rejects_unchanged_right_and_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / f'{i}.xwd' for i in range(4)]
            home, dex = rows(0), rows(80)
            for path, data in zip(paths, (home, dex, dex, dex)):
                make_xwd(path, data)
            with self.assertRaisesRegex(AssertionError, 'Right'):
                c148.verify(*paths)

    def test_rejects_no_b(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / f'{i}.xwd' for i in range(4)]
            home, dex = rows(0), rows(80)
            next_entry = rows(80)
            next_entry[250] = bytes([200, 200, 200]) * 256
            for path, data in zip(paths, (home, dex, next_entry, next_entry)):
                make_xwd(path, data)
            with self.assertRaisesRegex(AssertionError, 'B'):
                c148.verify(*paths)

    def test_rejects_invalid_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.xwd'
            path.write_bytes(b'\0' * 100)
            with self.assertRaises(ValueError):
                c148.load_xwd(path)


if __name__ == '__main__':
    unittest.main()
