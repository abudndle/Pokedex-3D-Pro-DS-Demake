"""C138 real host-compiled previewStreamLoad/Draw regression; synthetic only in CI."""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ROSTER=tuple(i for i in range(734) if i not in (721,722,723,724))


def generate_fixture(root,uv_count=0):
    target=root/'nitrofs'/'preview'
    target.mkdir(parents=True)
    ds=(struct.pack('<4sHHII',b'DS3M',2,2,0,7)
        +struct.pack('<18h',0,0,0,4096,0,0,0,4096,0,
                                  0,0,0,4096,0,0,0,4096,0)
        +bytes((192,224,232))*2)
    uv=struct.pack('<4sHH',b'P3UV',1,2)+struct.pack('<12h',*( (0,0,4096,0,0,4096)*2 ))
    for id in ROSTER:
        (target/f'p{id:03d}.ds3m').write_bytes(ds)
    for id in ROSTER[:uv_count]:
        (target/f'p{id:03d}.p3uv').write_bytes(uv)


def compile_probe(exe):
    cc=shutil.which('cc')
    if not cc: raise RuntimeError('host C compiler unavailable')
    subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-O2',
        '-DC7_TEST_HOST','-I'+str(ROOT/'tools'/'host_stub'),'-I'+str(ROOT/'source'),
        str(ROOT/'source'/'preview_stream.c'),
        str(ROOT/'source'/'preview_chunk_stream.c'),
        str(ROOT/'source'/'model_uv.c'),
        str(ROOT/'tests'/'c138_native_preview_probe.c'),'-o',str(exe)],check=True)


class TestNativePreviewProbe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc'): raise unittest.SkipTest('host C compiler unavailable')

    def test_real_native_loader_all_730_synthetic_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); generate_fixture(root)
            exe=root/'probe';compile_probe(exe)
            result=subprocess.run([str(exe),'0'],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('730/730',result.stdout)

    def test_real_native_loader_49_matched_uvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);generate_fixture(root,uv_count=49)
            exe=root/'probe';compile_probe(exe)
            result=subprocess.run([str(exe),'49'],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('UV 49',result.stdout)

    def test_loader_fails_on_corrupt_native_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);generate_fixture(root)
            path=root/'nitrofs'/'preview'/'p729.ds3m'
            data=bytearray(path.read_bytes());struct.pack_into('<I',data,8,777)
            path.write_bytes(data)
            exe=root/'probe';compile_probe(exe)
            result=subprocess.run([str(exe),'0'],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('invalid native DS3M header',result.stderr)

    def test_loader_preserves_private_source_face_colors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);generate_fixture(root)
            exe=root/'probe';compile_probe(exe)
            path=root/'nitrofs'/'preview'/'p730.ds3m'
            data=bytearray(path.read_bytes())
            # Two source triangles, then two original RGB888 triplets.
            first_color=16+2*18
            data[first_color:first_color+3]=bytes((14,22,105))
            path.write_bytes(data)
            result=subprocess.run([str(exe),'0'],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('XYZ/RGB/UV',result.stdout)

    def test_loader_fails_on_truncated_source_colors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);generate_fixture(root)
            path=root/'nitrofs'/'preview'/'p729.ds3m'
            path.write_bytes(path.read_bytes()[:-1])
            exe=root/'probe';compile_probe(exe)
            result=subprocess.run([str(exe),'0'],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)

    def test_loader_detects_modified_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);generate_fixture(root)
            exe=root/'probe';compile_probe(exe)
            # Altering geometry keeps a valid DS3M and is expected to load
            # and draw EXACT changed source bytes (not an invented mesh).
            path=root/'nitrofs'/'preview'/'p730.ds3m'
            data=bytearray(path.read_bytes());struct.pack_into('<h',data,16,1111)
            path.write_bytes(data)
            result=subprocess.run([str(exe),'0'],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()