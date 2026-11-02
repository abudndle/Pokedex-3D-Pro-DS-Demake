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
