"""C258 synthetic Records tab navigation tests, no original game assets."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c258_melonds_records_tabs_gate import verify_records_tabs
from test_c254_melonds_nav_gate import make
from test_c257_melonds_settings_gate import patch


class C258RecordsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.paths = [Path(tmp.name) / f'{n}.xwd' for n in ('home', 'regions', 'recent', 'quizzes', 'back')]
        for p, variant in zip(self.paths, ('home', 'dex', 'dex', 'dex', 'home')):
            make(p, variant)
        patch(self.paths[2], (30, 280, 155, 296), 210)
        patch(self.paths[2], (30, 120, 155, 150), 210)
        patch(self.paths[3], (30, 280, 155, 296), 240)
        patch(self.paths[3], (30, 120, 155, 150), 240)

    def test_all_tabs_and_b(self):
        result = verify_records_tabs(*self.paths)
        self.assertFalse(result['save_persistence_verified'])

    def test_records_not_open(self):
        make(self.paths[1], 'home')
        with self.assertRaisesRegex(ValueError, 'Records did not open'):
            verify_records_tabs(*self.paths)

    def test_recent_not_changed(self):
        self.paths[2].write_bytes(self.paths[1].read_bytes())
        with self.assertRaisesRegex(ValueError, 'regions_to_recent'):
            verify_records_tabs(*self.paths)

    def test_quizzes_not_changed(self):
        self.paths[3].write_bytes(self.paths[2].read_bytes())
        with self.assertRaisesRegex(ValueError, 'recent_to_quizzes'):
            verify_records_tabs(*self.paths)

    def test_b_did_not_return(self):
        make(self.paths[4], 'dex')
        with self.assertRaisesRegex(ValueError, 'B did not restore'):
            verify_records_tabs(*self.paths)


if __name__ == '__main__':
    unittest.main()
