"""Asset-free host build and original P3SK native skeleton load fixtures."""
import pathlib
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
SKELETON_RECORD=struct.Struct('<12fII')
HEADER=struct.Struct('<4sHHHHII')

def fixture(model_id,*,badparent=False,nan=False,suffix=False):
    names=b'SomeBoneRoot\0Base\0' if suffix else b'BoneRoot\0Base\0'
    off2=4 if suffix else 0
    off1=len(names)-5
    identity=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.]
    shifted=[1.,0.,0.,2.,0.,1.,0.,3.,0.,0.,1.,4.]
    node0=SKELETON_RECORD.pack(*identity,(1<<16)|65535,off1)
    node1=SKELETON_RECORD.pack(*shifted,(1<<16)|(2 if badparent else 0),off2)
    if nan:
        rec=bytearray(node1)
        struct.pack_into('<I',rec,0,0x7fc00000)
        node1=bytes(rec)
    payload=node0+node1+names
    return HEADER.pack(b'P3SK',1,model_id,2,1,len(names),zlib.crc32(payload))+payload

class C149HostSkeletonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.root=pathlib.Path(cls.tmp.name)
        cls.exe=cls.root/'skeleton-probe'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',
            '-I'+str(ROOT/'source'),str(ROOT/'source'/'original_skeleton.c'),
            str(ROOT/'tests'/'c149_skeleton_probe.c'),'-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_synthetic_730_model_native_skeletons(self):
        folder=self.root/'skeleton';folder.mkdir(exist_ok=True)
        for model in range(734):
            if 721<=model<=724:continue
            (folder/f'p{model:03d}.p3sk').write_bytes(fixture(model))
        out=subprocess.run([str(self.exe),'--all',str(folder),'1460','730'],text=True,capture_output=True)
        self.assertEqual(out.returncode,0,out.stderr)
        self.assertIn('models=730',out.stdout)

    def test_source_suffix_interned_name_is_valid(self):
        path=self.root/'suffix.p3sk';path.write_bytes(fixture(14,suffix=True))
        out=subprocess.run([str(self.exe),'--single',str(path),'14','1'],text=True,capture_output=True)
        self.assertEqual(out.returncode,0,out.stderr)

    def test_corrupt_crc_parent_matrix_or_wrong_model_fails_closed(self):
        for key,raw in (('parent',fixture(14,badparent=True)),('nan',fixture(14,nan=True)),
                        ('crc',fixture(14)[:-1]+b'X')):
            path=self.root/(key+'.p3sk');path.write_bytes(raw)
            out=subprocess.run([str(self.exe),'--single',str(path),'14','0'],text=True,capture_output=True)
            self.assertEqual(out.returncode,0,(key,out.stderr))
        valid=self.root/'valid.p3sk';valid.write_bytes(fixture(14))
        out=subprocess.run([str(self.exe),'--single',str(valid),'15','0'],text=True,capture_output=True)
        self.assertEqual(out.returncode,0,out.stderr)

    def test_missing_or_truncated_source_rig_fails_closed(self):
        truncated=self.root/'truncated.p3sk';truncated.write_bytes(fixture(17)[:-5])
        for path in (truncated,self.root/'missing.p3sk'):
            out=subprocess.run([str(self.exe),'--single',str(path),'17','0'],text=True,capture_output=True)
            self.assertEqual(out.returncode,0,out.stderr)

if __name__=='__main__':unittest.main()