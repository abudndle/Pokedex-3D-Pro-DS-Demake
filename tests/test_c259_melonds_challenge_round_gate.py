"""C259 synthetic Challenge round and B navigation tests."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c259_melonds_challenge_round_gate import verify_challenge_round
from test_c254_melonds_nav_gate import make
from test_c257_melonds_settings_gate import patch


class C259ChallengeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.paths = [Path(tmp.name) / f'{n}.xwd' for n in ('home','picker','question','review','continued','back')]
        for p, variant in zip(self.paths, ('home','dex','dex','dex','dex','home')):
            make(p, variant)
        for i, val in ((2, 135), (3, 195), (4, 235)):
            patch(self.paths[i], (35, 90, 185, 150), val)
            patch(self.paths[i], (35, 300, 185, 370), val)

    def test_full_round_and_return(self):
        result = verify_challenge_round(*self.paths)
        self.assertFalse(result['scoring_correctness_verified'])

    def test_picker_not_open(self):
        make(self.paths[1], 'home')
        with self.assertRaisesRegex(ValueError, 'picker'):
            verify_challenge_round(*self.paths)

    def test_question_not_started(self):
        self.paths[2].write_bytes(self.paths[1].read_bytes())
        with self.assertRaisesRegex(ValueError, 'question'):
            verify_challenge_round(*self.paths)

    def test_review_not_shown(self):
        self.paths[3].write_bytes(self.paths[2].read_bytes())
        with self.assertRaisesRegex(ValueError, 'review'):
            verify_challenge_round(*self.paths)

    def test_continue_not_advanced(self):
        self.paths[4].write_bytes(self.paths[3].read_bytes())
        with self.assertRaisesRegex(ValueError, 'continued'):
            verify_challenge_round(*self.paths)

    def test_b_not_home(self):
        make(self.paths[5], 'dex')
        with self.assertRaisesRegex(ValueError, 'B did not restore'):
            verify_challenge_round(*self.paths)


if __name__ == '__main__':
    unittest.main()
