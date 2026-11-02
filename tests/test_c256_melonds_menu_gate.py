"""C256 synthetic Challenge/Records/Album navigation and B regressions."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c256_melonds_menu_gate import verify_pages
from test_c254_melonds_nav_gate import make


class C256MenuTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        names = ('home', 'challenge', 'cback', 'records', 'rback', 'album', 'aback')
        self.paths = [Path(self.tmp.name) / (x + '.xwd') for x in names]
        for p, variant in zip(self.paths, ('home', 'dex', 'home', 'dex', 'home', 'dex', 'home')):
            make(p, variant)

    def test_all_three_pages_and_b(self):
        result = verify_pages(*self.paths)
        self.assertFalse(result['save_persistence_verified'])

    def test_challenge_not_open_rejected(self):
        make(self.paths[1], 'home')
        with self.assertRaisesRegex(ValueError, 'challenge did not'):
            verify_pages(*self.paths)

    def test_records_not_open_rejected(self):
        make(self.paths[3], 'home')
        with self.assertRaisesRegex(ValueError, 'records did not'):
            verify_pages(*self.paths)

    def test_album_not_open_rejected(self):
        make(self.paths[5], 'home')
        with self.assertRaisesRegex(ValueError, 'album did not'):
            verify_pages(*self.paths)

    def test_b_does_not_return_home_rejected(self):
        make(self.paths[4], 'dex')
        with self.assertRaisesRegex(ValueError, 'records B did not'):
            verify_pages(*self.paths)


if __name__ == '__main__':
    unittest.main()
