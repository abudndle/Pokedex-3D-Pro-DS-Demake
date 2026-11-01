"""C151 original animation owner/node binding on synthetic P3SK fixtures."""
import pathlib
import subprocess
import tempfile
import unittest
from test_c149_original_skeleton_loader import fixture

ROOT=pathlib.Path(__file__).resolve().parents[1]
class C151OriginalTrackBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.root=pathlib.Path(cls.tmp.name)
        cls.exe=cls.root/'track-binding'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',
            '-I'+str(ROOT/'source'),str(ROOT/'source'/'original_skeleton.c'),
            str(ROOT/'source'/'original_track_binding.c'),
            str(ROOT/'tests'/'c151_original_track_binding.c'),
            '-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_exact_original_node_index_and_name(self):
        path=self.root/'normal.p3sk';path.write_bytes(fixture(14))
        run=subprocess.run([str(self.exe),str(path)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
    def test_source_suffix_interning(self):
        path=self.root/'suffix.p3sk';path.write_bytes(fixture(14,suffix=True))
        run=subprocess.run([str(self.exe),str(path)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)

if __name__=='__main__':unittest.main()
