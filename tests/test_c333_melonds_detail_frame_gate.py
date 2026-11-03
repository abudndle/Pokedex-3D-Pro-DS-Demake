"""C333 prove frame acceptance rejects fake detail opens and reset changes."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from c333_melonds_detail_frame_gate import check_dex_detail
from test_c262_melonds_challenge_phase_gate import make_frame

class C333FrameTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.before=root/'entry.xwd'
        self.details=root/'detail.xwd'
        self.resumed=root/'resumed.xwd'
        make_frame(self.before,stage=0)
        make_frame(self.details,stage=1)
        shutil.copyfile(self.details,self.resumed)

    def test_view_opens_and_persists(self):
        a=check_dex_detail(self.before,self.details,self.resumed)
        self.assertGreater(a['detail_opened_lower_samples'],30)
        self.assertEqual(a['reboot_lower_changed_samples'],0)

    def test_no_detail_change_is_rejected(self):
        self.details.write_bytes(self.before.read_bytes())
        with self.assertRaisesRegex(ValueError,'did not open'):
            check_dex_detail(self.before,self.details,self.resumed)

    def test_wrong_reopened_tab_is_rejected(self):
        make_frame(self.resumed,stage=2)
        with self.assertRaisesRegex(ValueError,'changed across boot'):
            check_dex_detail(self.before,self.details,self.resumed)

    def test_invalid_capture_rejected(self):
        make_frame(self.resumed,stage=1,width=280)
        with self.assertRaisesRegex(ValueError,'geometry'):
            check_dex_detail(self.before,self.details,self.resumed)

    def test_missing_capture_rejected(self):
        self.resumed.write_bytes(b'')
        with self.assertRaises(ValueError):
            check_dex_detail(self.before,self.details,self.resumed)

if __name__=='__main__':
    unittest.main()
