"""Synthetic-only tests for C357 original GUI scene transforms."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from c357_gui_scene_transforms import recover, parse_scene_transforms

EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))


def fixture(name, *, badfloat=False, badspan=False, badtail=False, other_page=False):
    n = (16 if name == 'gui_title' else 5 if name == 'gui_common' else
         11 if name == 'en/gui_title' else 10 if name == 'jp/gui_title' else 3)
    inner_offset=160
    section_offset=120
    section_end=section_offset + n*56 + int(badspan)
    inner=bytearray(section_offset+n*56+int(badspan))
    inner[:4]=b'\xc5\x78\x00\x02'
    struct.pack_into('<I',inner,4,len(inner))
    struct.pack_into('<II',inner,0x38,section_offset,section_end)
    for i in range(n):
        offset=section_offset+i*56
        x = 64.0 if (other_page and i==1) else i*12.0
        values=[1.0,0.0,0.0,x, 0.0,1.0,0.0,float(-i), 0.0,0.0,1.0,0.0]
        if badfloat and i==1: values[3]=float('nan')
        struct.pack_into('<12f',inner,offset,*values)
        struct.pack_into('<II',inner,offset+48,65536 if i else 1179647,
                         44 if not badtail else 0xffffffff)
    root=bytearray(inner_offset)+inner
    root[:4]=b'\xc5\x78\x00\x01'
    struct.pack_into('<II',root,4,len(root)-120,256)
    struct.pack_into('<I',root,0x68,inner_offset)
    root.extend(b'\0'*256)
    return bytes(root)


def write_source(target, **options):
    with zipfile.ZipFile(target,'w') as z:
        for name in EXPECTED:
            z.writestr(f'decoded_c5/gui/{name}.c5',fixture(name,
                other_page=(options.get('different_languages') and name=='jp/gui01')))


class C357Tests(unittest.TestCase):
    def test_exact_56_byte_source_matrix_and_tail(self):
        source=fixture('gui_title')
        result=parse_scene_transforms(source)
        self.assertEqual(result['count'],16)
        self.assertEqual(result['source_section_start'],280)
        self.assertEqual(result['source_section_end'],280+16*56)
        second=result['transforms'][1]
        self.assertEqual(second['source_matrix_offset'],280+56)
        self.assertEqual(second['matrix_rows'][0],[1.0,0.0,0.0,12.0])
        self.assertEqual(second['translation'],[12.0,-1.0,0.0])
        self.assertEqual(second['tail_hex'],['00000100','2c000000'])
        raw=source[second['source_matrix_offset']:second['source_matrix_offset']+56]
        self.assertEqual(second['source_record_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertFalse(second['authentic_screen_pixel_coordinates_verified'])

    def test_six_language_pairs_have_identical_transform_sources(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';write_source(src)
            report=recover(src)
            self.assertEqual(report['original_c5_resources'],16)
            self.assertEqual(report['original_transform_records'],78)
            self.assertEqual(report['identical_en_jp_numbered_gui_transform_pairs'],6)
            self.assertEqual(report['per_resource_transform_counts']['gui_title'],16)
            self.assertEqual(report['per_resource_transform_counts']['en/gui_title'],11)
            self.assertEqual(report['per_resource_transform_counts']['jp/gui_title'],10)
            self.assertFalse(report['native_3ds_coordinates_calibrated_to_DS_pixels'])
            self.assertFalse(report['release_ready'])

    def test_language_mismatch_rejected_not_pretended_shared(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';write_source(src,different_languages=True)
            with self.assertRaisesRegex(ValueError,'different original EN/JP'):
                recover(src)

    def test_reject_nan_original_matrix(self):
        with self.assertRaisesRegex(ValueError,'nonfinite'):
            parse_scene_transforms(fixture('gui_title',badfloat=True))

    def test_reject_misaligned_scene_transform_section(self):
        with self.assertRaisesRegex(ValueError,'56-byte'):
            parse_scene_transforms(fixture('gui_title',badspan=True))

    def test_reject_unknown_tail_is_not_assigned_semantics(self):
        report=parse_scene_transforms(fixture('gui_title',badtail=True))
        self.assertEqual(report['transforms'][1]['tail_hex'][1],'ffffffff')
        self.assertFalse(report['transform_tail_semantics_decoded'])

    def test_reject_wrong_embedded_magic(self):
        data=bytearray(fixture('gui_title'))
        data[160]=0
        with self.assertRaisesRegex(ValueError,'embedded C5'):
            parse_scene_transforms(bytes(data))

    def test_reject_embedded_section_exceeding_metadata(self):
        data=bytearray(fixture('gui_title'))
        struct.pack_into('<I',data,160+0x3c,0xfffffffe)
        with self.assertRaisesRegex(ValueError,'section bounds'):
            parse_scene_transforms(bytes(data))

    def test_reject_missing_original_source(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip'
            with zipfile.ZipFile(src,'w') as z:
                z.writestr('decoded_c5/gui/gui_title.c5',fixture('gui_title'))
            with self.assertRaisesRegex(ValueError,'missing'):
                recover(src)

    def test_reject_duplicate_archive_paths(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';write_source(src)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(src,'a') as z:
                    z.writestr('decoded_c5/gui/gui_title.c5',fixture('gui_title'))
            with self.assertRaisesRegex(ValueError,'duplicate'):
                recover(src)

    def test_reject_source_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';write_source(src)
            link=Path(d)/'linked.zip';link.symlink_to(src)
            with self.assertRaisesRegex(ValueError,'symlink'):
                recover(link)


if __name__=='__main__':
    unittest.main()
