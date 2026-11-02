"""C255 synthetic DS AR-disabled and Move Dex navigation regressions."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c255_melonds_ds_ar_gate import verify_ds_ar_and_move
from test_c254_melonds_nav_gate import make


class C255DSMenuTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = [Path(self.tmp.name) / (x + '.xwd') for x in ('home', 'ar', 'move', 'back')]
        for p, variant in zip(self.paths, ('home', 'home', 'dex', 'home')):
            make(p, variant)

    def test_disabled_ar_and_move_dex_then_b(self):
        result = verify_ds_ar_and_move(*self.paths)
        self.assertFalse(result['dsi_camera_verified'])

    def test_disabled_ar_one_row_scroll_keeps_menu(self):
        # Actual C255 melonDS capture scrolls the five visible labels up
        # 16px when selecting disabled AR. A strict same-position gate
        # incorrectly rejected that valid HOME behavior.
        from test_c254_melonds_nav_gate import WIDTH
        import struct
        home = bytearray(self.paths[0].read_bytes())
        for y in range(310, 377):
            for x in range(20, 205):
                off = 100 + (y * WIDTH + x) * 4
                value = 200 if (y // 16) % 2 else 80
                home[off:off+4] = bytes((value, value, value, 255))
        self.paths[0].write_bytes(home)
        self.paths[3].write_bytes(home)
        scrolled = bytearray(home)
        for y in range(294, 361):
            dest = 100 + (y * WIDTH + 20) * 4
            src = 100 + ((y + 16) * WIDTH + 20) * 4
            scrolled[dest:dest + 185*4] = home[src:src + 185*4]
        self.paths[1].write_bytes(scrolled)
        result = verify_ds_ar_and_move(*self.paths)
        self.assertEqual(result['disabled_ar_scrolled_label_delta'], 0)

    def test_ar_entering_page_rejected(self):
        make(self.paths[1], 'dex')
        with self.assertRaisesRegex(ValueError, 'AR Viewer unexpectedly'):
            verify_ds_ar_and_move(*self.paths)

    def test_move_dex_not_entered_rejected(self):
        make(self.paths[2], 'home')
        with self.assertRaisesRegex(ValueError, 'Move Dex did not'):
            verify_ds_ar_and_move(*self.paths)

    def test_b_did_not_restore_home_rejected(self):
        make(self.paths[3], 'dex')
        with self.assertRaisesRegex(ValueError, 'B did not'):
            verify_ds_ar_and_move(*self.paths)


if __name__ == '__main__':
    unittest.main()
