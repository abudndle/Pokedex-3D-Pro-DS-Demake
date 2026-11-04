"""C349 synthetic-only regression tests for private ROM menu navigation."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c349_private_navigation_gate import verify


def frame(path, page=0, selected=0):
    width, height = 256, 384
    head = [0] * 25
    head[0], head[3], head[4], head[5] = 100, 24, width, height
    head[7], head[11], head[12] = 0, 32, width * 4
    head[14:17] = [0xff0000, 0x00ff00, 0x0000ff]
    body = bytearray(width * height * 4)
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 4
            # Vary the lower screen strongly when switching HOME and Dex.
            base = (40, 180, 240) if (y >= 192 and page == 0) else (80, 40, 60)
            # Vary only a small lower number area on DS Right.
            if page == 1 and y >= 192 and selected and 80 <= x < 104 and 276 <= y < 300:
                base = (230, 210, 30)
            body[offset:offset + 4] = bytes((*base, 255))
    path.write_bytes(struct.pack('>25I', *head) + body)


class C349Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home, self.dex, self.browse, self.back = [
            self.root / name for name in ('home.xwd', 'dex.xwd', 'next_dex.xwd', 'back.xwd')]
        frame(self.home)
        frame(self.dex, page=1)
        frame(self.browse, page=1, selected=1)
        frame(self.back)

    def check(self):
        return verify(self.home, self.dex, self.browse, self.back, self.root / 'report.json')

    def test_real_transitions_required_before_evidence_accepted(self):
        result = self.check()
        self.assertTrue(result['private_asset_integrated_rom_navigation'])
        self.assertFalse(result['original_gui_parity_verified'])
        self.assertFalse(result['release_ready'])
        self.assertEqual(result['back_to_home_changed_lower_sample_pixels'], 0)
        self.assertEqual(len(json.loads((self.root / 'report.json').read_text())['frames_sha256']), 4)

    def test_stuck_at_home_rejected(self):
        frame(self.dex)
        with self.assertRaisesRegex(ValueError, 'did not visibly open Dex'):
            self.check()
        self.assertFalse((self.root / 'report.json').exists())

    def test_right_no_effect_rejected(self):
        frame(self.browse, page=1)
        with self.assertRaisesRegex(ValueError, 'did not visibly change'):
            self.check()
        self.assertFalse((self.root / 'report.json').exists())

    def test_b_does_not_return_rejected(self):
        frame(self.back, page=1)
        with self.assertRaisesRegex(ValueError, 'did not visibly restore'):
            self.check()
        self.assertFalse((self.root / 'report.json').exists())

    def test_existing_report_not_overwritten(self):
        target = self.root / 'report.json'
        target.write_text('original')
        with self.assertRaisesRegex(ValueError, 'must not exist'):
            self.check()
        self.assertEqual(target.read_text(), 'original')


if __name__ == '__main__':
    unittest.main()
