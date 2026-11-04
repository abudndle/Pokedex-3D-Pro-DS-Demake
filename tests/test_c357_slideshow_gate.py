from pathlib import Path
import tempfile
import unittest
from test_c355_album_view_gate import capture
from c357_slideshow_gate import verify_frames


class SlideshowGateTests(unittest.TestCase):
    def test_reject_missing_advance_pause_touch_and_reboot(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/f'{i}.xwd' for i in range(12)]
            ids=(9,9,8,8,8,7,6,6,6,5,9,None)
            for p,n in zip(paths,ids):capture(p,n)
            self.assertTrue(verify_frames(*paths)['timed_advance'])
            for i in range(11):
                capture(paths[i],1)
                with self.assertRaises(ValueError):verify_frames(*paths)
                capture(paths[i],ids[i])
            capture(paths[-1],9)
            with self.assertRaises(ValueError):verify_frames(*paths)


if __name__=='__main__':unittest.main()
