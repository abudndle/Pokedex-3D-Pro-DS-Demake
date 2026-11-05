"""C357 synthetic-only tests for C5 v2 original GUI scene transforms."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from c357_gui_source_transforms import EXPECTED, EXPECTED_COUNTS, decode_source_transforms, recover


def fixture(key, *, alter_translation=False, nonfinite=False, badrange=False):
    n = EXPECTED_COUNTS[key]
    inner_offset = 0xa0
    nested_len = 0x78 + 56*n
    gpu_start = inner_offset + nested_len
    raw = bytearray(gpu_start + 256)
    raw[:4] = b'\xc5\x78\x00\x01'
    struct.pack_into('<II', raw, 4, gpu_start - 0x78, 256)
    struct.pack_into('<I', raw, 0x68, inner_offset)
    raw[inner_offset:inner_offset+4] = b'\xc5\x78\x00\x02'
    struct.pack_into('<I', raw, inner_offset+4, nested_len)
    struct.pack_into('<II', raw, inner_offset+0x38, 0x78,
                     0x78+56*n+4 if badrange else 0x78+56*n)
    for i in range(n):
        y = float(i*2+(1 if alter_translation else 0))
        coeff = (1,0,0,20, 0,1,0,y, 0,0,1,-5)
        offset = inner_offset + 0x78 + i*56
        struct.pack_into('<12f2I', raw, offset, *coeff, 0x00010000, i+1)
    if nonfinite:
        struct.pack_into('<I', raw, inner_offset + 0x78, 0x7f800000)
    return bytes(raw)


def archive(path, *, missing=None, duplicate=False, mismatch=False, unsafe=False):
    with zipfile.ZipFile(path, 'w') as z:
        for key in EXPECTED:
            name = f'decoded_c5/gui/{key}.c5'
            if name != missing:
                z.writestr(name, fixture(key, alter_translation=mismatch and key=='jp/gui01'))
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr('decoded_c5/gui/gui_common.c5', fixture('gui_common'))
        if unsafe:
            z.writestr('../unsafe', b'bad')


class C357Tests(unittest.TestCase):
    def test_decode_source_matrix_and_opaque_fields_exactly(self):
        raw = fixture('gui_common')
        report = decode_source_transforms(raw)
        self.assertEqual(report['source_transform_records'], 5)
        item = report['transforms'][1]
        self.assertEqual(item['source_translation_xyz'], [20,2,-5])
        self.assertEqual(item['matrix_3x4_row_major'][0], [1,0,0,20])
        self.assertEqual(item['opaque_original_metadata_words'], ['00010000','00000002'])
        pos = item['original_c5_byte_offset']
        self.assertEqual(item['original_transform_record_sha256'],hashlib.sha256(raw[pos:pos+56]).hexdigest())
        self.assertFalse(item['original_screen_pixel_position_proven'])

    def test_original_roster_78_and_language_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'original.zip';archive(source)
            report=recover(source)
            self.assertEqual(report['original_c5_resources'], 16)
            self.assertEqual(report['source_observed_transform_records'], 78)
            self.assertEqual(report['source_title_scene_transforms'], 37)
            self.assertEqual(report['matching_japanese_english_gui_page_sections'],6)
            self.assertFalse(report['source_scene_to_screen_projection_decoded'])
            self.assertFalse(report['original_home_touch_geometry_verified'])
            self.assertFalse(report['release_ready'])

    def test_reject_nonfinite_source_transform(self):
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            decode_source_transforms(fixture('gui_title', nonfinite=True))

    def test_reject_non_56_byte_scene_section(self):
        with self.assertRaisesRegex(ValueError, '56-byte'):
            decode_source_transforms(fixture('gui_title', badrange=True))

    def test_reject_inner_header_outside_metadata(self):
        raw=bytearray(fixture('gui_title'))
        struct.pack_into('<I', raw, 0x68, len(raw)-40)
        with self.assertRaisesRegex(ValueError, 'outside C5 metadata'):
            decode_source_transforms(bytes(raw))

    def test_reject_source_metadata_gpu_overlap(self):
        raw=bytearray(fixture('gui_title'))
        struct.pack_into('<I', raw, 8, 1)
        with self.assertRaisesRegex(ValueError, 'metadata/GPU extents'):
            decode_source_transforms(bytes(raw))

    def test_reject_different_numbered_english_japanese_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'original.zip';archive(src,mismatch=True)
            with self.assertRaisesRegex(ValueError, 'transforms differ'):
                recover(src)

    def test_reject_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'original.zip';archive(src,missing='decoded_c5/gui/en/gui03.c5')
            with self.assertRaisesRegex(ValueError, 'missing or oversized'):
                recover(src)

    def test_reject_duplicate_member_and_zip_slip(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'source.zip';archive(src,duplicate=True)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                recover(src)
            src2=Path(tmp)/'malicious.zip';archive(src2,unsafe=True)
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                recover(src2)

    def test_reject_symlink_source_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.zip';archive(source)
            link=Path(tmp)/'alias.zip';link.symlink_to(source)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                recover(link)


if __name__ == '__main__':
    unittest.main()
