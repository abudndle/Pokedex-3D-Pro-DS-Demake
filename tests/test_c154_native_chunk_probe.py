"""C154 source-only synthetic tests for actual C P3CS loader & exact data decode."""
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'source'
if not SOURCE.exists():
    SOURCE = ROOT/'staging'/'public_source_mirror'


def fixture(model, chunks=1):
    table=bytearray(); payload=bytearray(); cursor=24+chunks*16; tri=0
    for j in range(chunks):
        records=bytearray()
        for k in range(2):
            xyz=[((model+j+k+i)%701)-351 for i in range(9)]
            uv=[((model+j+k+i*3)%16382)-8191 for i in range(6)]
            rgb=bytes(((model+j+k+i*17)&255) for i in range(3))
            records+=struct.pack('<9h6h',*xyz,*uv)+rgb
        table+=struct.pack('<IHHII',tri,2,0,cursor,zlib.crc32(records))
        payload+=records;cursor+=len(records);tri+=2
    head=struct.pack('<4s4H3I',b'P3CS',1,model,chunks,0,tri,tri+13,zlib.crc32(table))
    return head+table+payload


class TestC154NativeChunkProbe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc'):
            raise unittest.SkipTest('host C compiler unavailable')
        cls.tmp=tempfile.TemporaryDirectory()
        cls.base=Path(cls.tmp.name)
        cls.exe=cls.base/'probe'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',
                        '-I'+str(SOURCE),str(SOURCE/'preview_chunk_stream.c'),
                        str(ROOT/'tests'/'c154_chunk_probe.c') if (ROOT/'tests').exists()
                            else str(ROOT/'public_tests'/'c154_chunk_probe.c'),
                        '-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    def check(self, paths, nmodel, nchunk, nface, success=True):
        result=subprocess.run([str(self.exe),'--all',str(paths),str(nmodel),
                               str(nchunk),str(nface)],capture_output=True,text=True)
        self.assertEqual(result.returncode==0,success,(result.stdout,result.stderr))
    def test_500_source_models_exact_native_xyz_uv_rgb(self):
        root=self.base/'all';root.mkdir(exist_ok=True)
        for i in range(500):
            (root/f'p{i:03d}.p3cs').write_bytes(fixture(i,1+i%3))
        self.check(root,500,999,1998)
    def test_refuses_corrupt_source_chunk_data(self):
        root=self.base/'bad';root.mkdir(exist_ok=True)
        b=bytearray(fixture(5));b[-1]^=0x80
        (root/'p005.p3cs').write_bytes(b)
        self.check(root,1,1,2,False)
    def test_refuses_wrong_source_model_id(self):
        root=self.base/'wrong';root.mkdir(exist_ok=True)
        (root/'p008.p3cs').write_bytes(fixture(7))
        self.check(root,1,1,2,False)
    def test_refuses_truncated_source_chunk_table(self):
        root=self.base/'truncated';root.mkdir(exist_ok=True)
        (root/'p009.p3cs').write_bytes(fixture(9)[:30])
        self.check(root,1,1,2,False)


if __name__=='__main__':unittest.main()