"""C151 synthetic original-owner P3TB/P3SK contract; no Nintendo assets."""
import pathlib
import struct
import subprocess
import tempfile
import unittest
import zlib
from test_c149_original_skeleton_loader import fixture

ROOT=pathlib.Path(__file__).resolve().parents[1]
HEADER=struct.Struct('<4sHHHHII')
RECORD=struct.Struct('<HHI104s')

def binding(rig,model=14,records=None,skeleton_crc=None,payload_crc=None):
    if records is None:records=[(1,0,3,b'BoneRoot')]
    payload=b''.join(RECORD.pack(*rec) for rec in records)
    if skeleton_crc is None:skeleton_crc=zlib.crc32(rig[20:])
    if payload_crc is None:payload_crc=zlib.crc32(payload)
    return HEADER.pack(b'P3TB',1,model,len(records),0,skeleton_crc,payload_crc)+payload

class C151NativeTrackBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.root=pathlib.Path(cls.tmp.name)
        cls.exe=cls.root/'track-probe'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',
            '-I'+str(ROOT/'source'),str(ROOT/'source'/'original_skeleton.c'),
            str(ROOT/'source'/'source_track_bindings.c'),
            str(ROOT/'tests'/'c151_track_binding_probe.c'),'-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def check(self,tag,rig,track,expected,model=14):
        sk=self.root/(tag+'.p3sk');tb=self.root/(tag+'.p3tb')
        sk.write_bytes(rig)
        if track is not None:tb.write_bytes(track)
        elif tb.exists():tb.unlink()
        proc=subprocess.run([str(self.exe),str(sk),str(tb),str(model),'1' if expected else '0'],
                            text=True,capture_output=True)
        self.assertEqual(proc.returncode,0,tag+': '+proc.stdout+' '+proc.stderr)
    def test_exact_original_node_owner_name_and_model_switch(self):
        sk=fixture(14)
        self.check('valid',sk,binding(sk),True)
        suffix=fixture(14,suffix=True)
        self.check('suffix',suffix,binding(suffix,records=[(1,4,3,b'BoneRoot')]),True)
    def test_reject_missing_truncated_and_trailing(self):
        sk=fixture(14);good=binding(sk)
        self.check('missing',sk,None,False)
        self.check('truncated',sk,good[:-1],False)
        self.check('trailing',sk,good+b'X',False)
    def test_reject_wrong_crc_and_model(self):
        sk=fixture(14)
        self.check('crc',sk,binding(sk,payload_crc=0),False)
        self.check('rigcrc',sk,binding(sk,skeleton_crc=0),False)
        self.check('model',sk,binding(sk,model=15),False)
        altered=bytearray(binding(sk));altered[10]=1
        self.check('reserved',sk,bytes(altered),False)
    def test_reject_name_index_offset_duplicates_and_order(self):
        sk=fixture(14)
        bad=[('name',[(1,0,3,b'boneroot')]),
             ('offset',[(1,9,3,b'BoneRoot')]),
             ('index',[(0,0,3,b'BoneRoot')]),
             ('duplicate',[(1,0,3,b'BoneRoot'),(1,0,6,b'BoneRoot')]),
             ('order',[(1,0,6,b'BoneRoot'),(1,0,3,b'BoneRoot')]),
             ('nonzero-padding',[(1,0,3,b'BoneRoot\x00X')]),
             ('nonterminated',[(1,0,3,b'A'*104)])]
        for tag,records in bad:
            with self.subTest(tag=tag):self.check(tag,sk,binding(sk,records=records),False)
    def test_reject_zero_and_excessive_records(self):
        sk=fixture(14)
        self.check('zero',sk,binding(sk,records=[]),False)
        self.check('too-many',sk,binding(sk,records=[(1,0,i*3,b'BoneRoot') for i in range(3)]),False)

if __name__=='__main__':unittest.main()
