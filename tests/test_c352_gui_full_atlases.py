"""C352: synthetic-only original GUI PICA texture format regression tests."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c352_gui_full_atlases import (
    decode_pica_gui, texel_color, morton_index, recover, FORMAT_NAMES)
from test_c351_gui_texture_atlases import EXPECTED, synthetic_c5
from c351_gui_texture_atlases import descriptors


class C352Tests(unittest.TestCase):
    def test_format_tokens_cover_known_gui_c5(self):
        self.assertEqual(FORMAT_NAMES, {0x14016752: 'RGBA8',
            0x14016754: 'RGB8', 0x14016757: 'L8',
            0x14016758: 'LA8', 0x80336752: 'RGBA4'})

    def test_rgb8_source_bgr_channel_order(self):
        self.assertEqual(texel_color(b'\x03\x02\x01', 0, 'RGB8'), (1,2,3,255))

    def test_luminance_alpha8_alpha_first(self):
        self.assertEqual(texel_color(b'\x33\xa4', 0, 'LA8'), (164,164,164,51))

    def test_luminance8_opaque_grayscale(self):
        self.assertEqual(texel_color(b'\x22', 0, 'L8'), (34,34,34,255))

    def test_rgba4_color_nibbles_from_little_endian(self):
        self.assertEqual(texel_color(bytes((0x23,0xf1)), 0, 'RGBA4'),
                         (255,17,34,51))

    def test_morton_bottom_up_for_all_new_formats(self):
        samples = {
            0x14016754: ([0,0,99], [99,0,0,255]),
            0x14016757: ([73], [73,73,73,255]),
            0x14016758: ([101,43], [43,43,43,101]),
            0x80336752: ([0x2f,0x14], [17,68,34,255]),
        }
        for token, (sample, rgba) in samples.items():
            with self.subTest(token=hex(token)):
                out = decode_pica_gui(bytes(sample)*64, 8, 8, token)
                self.assertEqual(len(out), 8*8*4)
                self.assertEqual(list(out[:4]), rgba)
                self.assertEqual(list(out[-4:]), rgba)

    def test_morton_8x8_in_second_tile_and_vertical(self):
        raw = bytearray(16*8)
        for y in range(8):
            for x in range(16):
                raw[morton_index(x,y,16)] = x+y*16
        rgba = decode_pica_gui(bytes(raw),16,8,0x14016757)
        self.assertEqual(rgba[:4], bytes((112,112,112,255)))
        self.assertEqual(rgba[15*4:15*4+4], bytes((127,127,127,255)))
        self.assertEqual(rgba[7*16*4:7*16*4+4], bytes((0,0,0,255)))

    def test_reject_bad_dimensions_or_unknown_format(self):
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            decode_pica_gui(b'\0',8,8,0x14016754)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            decode_pica_gui(bytes(256),8,8,0xdeadcafe)

    def test_synthetic_all_132_source_textures_and_hashes(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            src = root/'input.zip'
            # Synthetic C5 source, no Nintendo bytes. The 35 original-like
            # RGBA8 entries remain, and 97 synthetic rows span other formats.
            nonrgba_index = 0
            with zipfile.ZipFile(src,'w') as z:
                for base in EXPECTED:
                    original = synthetic_c5(base)
                    rows,start = descriptors(original)
                    header = bytearray(original[:start])
                    gpu = bytearray()
                    for row in rows:
                        kind = int(row['token'],16)
                        if kind != 0x14016752:
                            kind = (0x14016757 if nonrgba_index < 14 else
                                    0x14016754 if nonrgba_index < 20 else
                                    0x80336752 if nonrgba_index < 25 else
                                    0x14016758)
                            nonrgba_index += 1
                        bpp = {0x14016752:4,0x14016758:2,0x14016757:1,
                               0x14016754:3,0x80336752:2}[kind]
                        length = row['width']*row['height']*bpp
                        offset = len(gpu)
                        struct.pack_into('<I',header,120+28*row['index'],offset)
                        struct.pack_into('<I',header,120+28*row['index']+12,length)
                        struct.pack_into('<I',header,120+28*row['index']+20,kind)
                        gpu.extend(bytes([row['index']%256])*length)
                    struct.pack_into('<I',header,8,len(gpu))
                    z.writestr(f'decoded_c5/gui/{base}.c5',bytes(header+gpu))
            self.assertEqual(nonrgba_index,97)
            report = recover(src,root/'out')
            self.assertEqual(report['source_c5_count'],16)
            self.assertEqual(report['source_texture_entries'],132)
            self.assertEqual(report['decoded_textures'],132)
            self.assertEqual(report['decoded_by_format'],
                {'RGBA8':35,'LA8':72,'L8':14,'RGB8':6,'RGBA4':5})
            self.assertFalse(report['original_dual_screen_ui_pages_ready'])
            self.assertFalse(report['original_game_release_ready'])
            self.assertEqual(len(list((root/'out').rglob('*.png'))),132)
            self.assertEqual(len(list((root/'out').rglob('*.rgb555'))),132)
            for row in report['entries']:
                p = root/'out'/row['png_path']
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                                 row['png_sha256'])
                self.assertEqual((root/'out'/row['ds_atlas_path']).stat().st_size,
                                 row['width']*row['height']*2)

    def test_source_missing_is_atomic(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); src = root/'input.zip'
            with zipfile.ZipFile(src,'w') as z:
                z.writestr('decoded_c5/gui/gui_title.c5',synthetic_c5('gui_title'))
            with self.assertRaisesRegex(ValueError,'missing or oversized'):
                recover(src,root/'stage')
            self.assertFalse((root/'stage').exists())

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);src=root/'input.zip';src.write_bytes(b'invalid')
            output=root/'stage';output.mkdir();(output/'keep').write_text('keep')
            with self.assertRaisesRegex(ValueError,'already exists'):
                recover(src,output)
            self.assertEqual((output/'keep').read_text(),'keep')

    def test_reject_symlink_source(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);src=root/'input.zip';src.write_bytes(b'invalid')
            alias=root/'link.zip';alias.symlink_to(src)
            with self.assertRaisesRegex(ValueError,'symlink'):
                recover(alias,root/'stage')

    def test_reject_duplicate_original_c5_members(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);src=root/'input.zip'
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(src,'w') as z:
                    z.writestr('decoded_c5/gui/gui_title.c5',synthetic_c5('gui_title'))
                    z.writestr('decoded_c5/gui/gui_title.c5',synthetic_c5('gui_title'))
            with self.assertRaisesRegex(ValueError,'duplicate'):
                recover(src,root/'out')


if __name__ == '__main__':
    unittest.main()
