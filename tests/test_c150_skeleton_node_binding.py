"""C150: exact original-source skeleton name binding without fake motion."""
import pathlib
import struct
import subprocess
import tempfile
import unittest
import zlib
from test_c149_original_skeleton_loader import fixture

ROOT=pathlib.Path(__file__).resolve().parents[1]

class SkeletonNodeBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.root=pathlib.Path(cls.tmp.name)
        cls.exe=cls.root/'node-binding'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',
            '-I'+str(ROOT/'source'),str(ROOT/'source'/'original_skeleton.c'),
            str(ROOT/'tests'/'c150_skeleton_node_binding.c'),'-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def check(self,name,data,expected):
        path=self.root/(name+'.p3sk')
        path.write_bytes(data)
        out=subprocess.run([str(self.exe),str(path),'1' if expected else '0'],
                           text=True,capture_output=True)
        self.assertEqual(out.returncode,0,out.stderr)
    def test_exact_original_node_and_parent_chain(self):
        self.check('normal',fixture(14),True)
    def test_original_suffix_interned_name(self):
        self.check('suffix',fixture(14,suffix=True),True)
    def test_reject_duplicate_source_name(self):
        data=bytearray(fixture(14))
        # Point the second node at the first node's exact source string.
        root_name=struct.unpack_from('<I',data,20+52)[0]
        struct.pack_into('<I',data,20+56+52,root_name)
        struct.pack_into('<I',data,16,zlib.crc32(data[20:]))
        self.check('duplicate',bytes(data),False)
    def test_reject_corrupt_parent_or_crc(self):
        self.check('parent',fixture(14,badparent=True),False)
        self.check('crc',fixture(14)[:-1]+b'X',False)

if __name__=='__main__':unittest.main()
