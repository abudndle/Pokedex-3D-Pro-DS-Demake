"""Synthetic-only C137 NitroFS preflight and staging tests."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from c137_private_nitrofs_preflight import audit, ROSTER
from c137_stage_private_nitrofs import stage


def ds3m(reserved=0, triangles=1):
    return (struct.pack('<4sHHII',b'DS3M',2,triangles,reserved,triangles)
            + bytes(18*triangles) + bytes((192,224,232))*triangles)


def make_zip(path, *, reserved=0, uv=False, malicious=None):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as out:
        for i in sorted(ROSTER):
            out.writestr(f'preview/p{i:03d}.ds3m',ds3m(reserved if i==0 else 0))
        out.writestr('textures/p000/t000.p3px',
                     struct.pack('<4sHHH',b'P3PX',2,8,8)+bytes(128))
        out.writestr('moves.p3dm',struct.pack('<4sHH',b'P3DM',1,559))
        out.writestr('data/dex_en.p3dx',struct.pack('<4sHH',b'P3DX',1,649)+bytes(649*256))
        if uv:
            out.writestr('preview/p000.p3uv',
                         struct.pack('<4sHH',b'P3UV',1,1)+bytes(12))
        if malicious:
            out.writestr(malicious,b'x')


class C137Tests(unittest.TestCase):
    def test_all_730_preview_headers_and_uvs_pass_not_release(self):
        with tempfile.TemporaryDirectory() as d:
            package=pathlib.Path(d)/'private.zip'
            make_zip(package,uv=True)
            result=audit(package,full_crc=True)
            self.assertTrue(result['native_preview_ready'])
            self.assertEqual(result['native_preview_count'],730)
            self.assertEqual(result['unit_uv_pairs_accepted'],1)
            self.assertFalse(result['original_release_ready'])
            self.assertEqual(result['source_sidecars_missing']['source_material_ranges'],730)
            self.assertTrue(result['missing_release_ui_and_text'])

    def test_reject_native_reserved_header_and_stage_does_not_modify_target(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            package=root/'bad.zip'
            make_zip(package,reserved=11)
            result=audit(package)
            self.assertFalse(result['native_preview_ready'])
            self.assertIn('preview/p000.ds3m',str(result['issues']))
            with self.assertRaisesRegex(ValueError,'preflight failed'):
                stage(package,root/'nitrofs')
            self.assertFalse((root/'nitrofs').exists())

    def test_reject_unsafe_zip_and_preserve_existing_staging(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            package=root/'unsafe.zip'
            make_zip(package,malicious='../outside')
            with self.assertRaisesRegex(ValueError,'unsafe'):
                audit(package)
            target=root/'stage'
            target.mkdir()
            (target/'original.txt').write_text('preserve')
            with self.assertRaisesRegex(ValueError,'already exists'):
                stage(package,target)
            self.assertEqual((target/'original.txt').read_text(),'preserve')

    def test_extract_exact_original_bytes_only_to_new_private_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            package=root/'qa.zip'
            make_zip(package,uv=True)
            target=root/'private-stage'
            result=stage(package,target)
            self.assertTrue(result['native_preview_ready'])
            self.assertFalse(result['original_release_ready'])
            self.assertEqual((target/'preview/p000.ds3m').read_bytes(),ds3m())
            self.assertEqual(len(list((target/'preview').glob('*.ds3m'))),730)
            self.assertEqual((target/'preview/p000.p3uv').stat().st_size,20)
            with self.assertRaisesRegex(ValueError,'already exists'):
                stage(package,target)

if __name__=='__main__':unittest.main()