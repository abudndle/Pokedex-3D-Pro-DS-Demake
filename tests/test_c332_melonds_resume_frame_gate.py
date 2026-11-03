"""C332 synthetic positive/negative dual-screen persistence frame gate."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c332_melonds_resume_frame_gate import verify_same_question
from test_c262_melonds_challenge_phase_gate import make_frame


class C332FrameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.before = Path(self.tmp.name) / 'before.xwd'
        self.after = Path(self.tmp.name) / 'after.xwd'
        make_frame(self.before, stage=1)
        shutil.copyfile(self.before, self.after)

    def test_same_real_question_image_accepted(self):
        result = verify_same_question(self.before, self.after)
        self.assertEqual(result['lower_changed_samples'], 0)
        self.assertFalse(result['dsi_hardware_verified'])

    def test_different_question_options_rejected(self):
        make_frame(self.after, stage=2)
        with self.assertRaisesRegex(ValueError, 'question changed'):
            verify_same_question(self.before, self.after)

    def test_top_only_save_status_change_ignored(self):
        data = bytearray(self.before.read_bytes())
        for y in range(70, 105):
            for x in range(50, 95):
                data[100 + (y*256+x)*4] = 250
        self.after.write_bytes(data)
        self.assertTrue(verify_same_question(self.before, self.after)
                        ['asset_free_second_question_continuity'])

    def test_nonstandard_capture_geometry_rejected(self):
        make_frame(self.after, stage=1, width=280)
        with self.assertRaisesRegex(ValueError, 'geometry changed'):
            verify_same_question(self.before, self.after)

    def test_truncated_capture_rejected(self):
        self.after.write_bytes(b'')
        with self.assertRaises(ValueError):
            verify_same_question(self.before, self.after)


if __name__ == '__main__':
    unittest.main()
