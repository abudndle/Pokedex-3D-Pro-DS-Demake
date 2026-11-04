"""C351 entirely synthetic source-C5 texture and PICA Morton decoder tests."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c351_gui_texture_atlases import (
    EXPECTED, TEXTURE_ENTRY, descriptors, decode_morton_abgr8,
    encode_rgba_png, quantize_a1rgb555, recover, KNOWN_BPP,
)

COUNTS = {'gui_title':1, 'gui_common':5, 'en/gui_title':1, 'jp/gui_title':1}
for scope in ('en','jp'):
    for n in range(1,7):COUNTS[f'{scope}/gui{n:02d}'] = 11 if n in (3,6) else 10


def synthetic_c5(key, *, badname=False, wrong_size=False, overlapping=False):
    count = COUNTS[key]
    reserved = bytearray(120+28*count)
    names = bytearray()
    gpu = bytearray()
    for i in range(count):
        # 35 32bpp textures across 16 original-like resource names.
        isrgba = ((key == 'gui_title' or key.endswith('/gui_title')) or
                  (key == 'gui_common' and i in (0,1)) or
                  (key.endswith(('gui01','gui02','gui03')) and i in (2,6)) or
                  (key.endswith(('gui04','gui05')) and i in (2,6,8)) or
                  (key.endswith('gui06') and i in (2,6,9)))
        token = 0x14016752 if isrgba else 0x14016758
        bpp = KNOWN_BPP[token]
        nbytes = 8*8*bpp//8
        offset = len(gpu)
        name = '../escape' if badname and i == 0 else f'ui_{i:02d}'
        name_ref = len(names)
        names.extend(name.encode()+b'\0')
        TEXTURE_ENTRY.pack_into(reserved,120+28*i,
            0 if overlapping and i==1 else offset, 0, name_ref,
            nbytes+1 if wrong_size and i==0 else nbytes,
            (8<<16)|8, token, 0x10001)
        gpu.extend(bytes([i%256,40,90,255]) * (nbytes//4))
    name_start=len(reserved)
    meta=len(reserved)+len(names)-120
    struct.pack_into('<4sII',reserved,0,b'\xc5\x78\x00\x01',meta,len(gpu))
    struct.pack_into('<I',reserved,12,count<<16)
    struct.pack_into('<I',reserved,0x58,120)
    struct.pack_into('<I',reserved,0x5c,120+28*count)
    struct.pack_into('<I',reserved,0x64,name_start)
    return bytes(reserved+names+gpu)


def archive(path, **kwargs):
    with zipfile.ZipFile(path,'w') as z:
        for key in EXPECTED:
            z.writestr(f'decoded_c5/gui/{key}.c5',synthetic_c5(key,**kwargs))


class C351Tests(unittest.TestCase):
    def test_full_fixture_creates_35_lossless_png_and_rgb555(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source.zip';archive(src)
            report=recover(src,root/'private')
            self.assertEqual(report['total_original_texture_descriptors'],132)
            self.assertEqual(report['confirmed_abgr8_rgba_atlases_decoded'],35)
            self.assertEqual(report['other_format_descriptors_preserved_undecoded'],97)
            self.assertFalse(report['complete_original_gui_format_coverage'])
            self.assertFalse(report['original_game_release_ready'])
            self.assertEqual(len(list((root/'private').rglob('*.png'))),35)
            self.assertEqual(len(list((root/'private').rglob('*.rgb555'))),35)
            self.assertEqual(len(json.loads((root/'private/C351_PRIVATE_TEXTURE_ATLASES.json').read_text())['texture_entries']),132)

    def test_morton_abgr_swizzle_color_and_bottom_up_orientation(self):
        w=h=8
        tiled=bytearray(w*h*4)
        for y in range(h):
            for x in range(w):
                ix=((x&1)|((y&1)<<1)|((x&2)<<1)|((y&2)<<2)|((x&4)<<2)|((y&4)<<3))
                tiled[ix*4:ix*4+4]=bytes((255,10+y,20+x,100+y))
        rgba=decode_morton_abgr8(bytes(tiled),w,h)
        self.assertEqual(rgba[:4],bytes((107,20,17,255)))
        self.assertEqual(rgba[(h-1)*w*4:(h-1)*w*4+4],bytes((100,20,10,255)))
        self.assertEqual(rgba[((h-1)*w+7)*4:((h-1)*w+7)*4+4],bytes((100,27,10,255)))

    def test_png_is_lossless_rgba(self):
        import zlib
        rgba=bytes((5,40,200,0))*64
        png=encode_rgba_png(rgba,8,8)
        self.assertTrue(png.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(png[12:16],b'IHDR')
        self.assertEqual(png[25],6)
        length=struct.unpack_from('>I',png,33)[0]
        self.assertEqual(zlib.decompress(png[41:41+length]),
                         b''.join(b'\0'+rgba[r*32:(r+1)*32] for r in range(8)))

    def test_a1rgb555_alpha_roundtrip(self):
        rgba=bytes((248,0,0,255,0,248,0,0,0,0,248,127,255,255,255,128))
        self.assertEqual(quantize_a1rgb555(rgba),
                         struct.pack('<4H',0x801f,0x03e0,0x7c00,0xffff))

    def test_reject_texture_length_mismatch(self):
        with self.assertRaisesRegex(ValueError,'invalid source C5 texture descriptor'):
            descriptors(synthetic_c5('en/gui01',wrong_size=True))

    def test_reject_overlapping_texture_range(self):
        with self.assertRaisesRegex(ValueError,'invalid source C5 texture descriptor'):
            descriptors(synthetic_c5('en/gui01',overlapping=True))

    def test_reject_unsafe_name(self):
        with self.assertRaisesRegex(ValueError,'unsafe or duplicate original GUI texture name'):
            descriptors(synthetic_c5('gui_title',badname=True))

    def test_reject_unknown_format_instead_of_guessing(self):
        raw=bytearray(synthetic_c5('gui_title'))
        struct.pack_into('<I',raw,120+20,0xdeadbeef)
        with self.assertRaisesRegex(ValueError,'invalid source C5 texture descriptor'):
            descriptors(bytes(raw))

    def test_reject_existing_private_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.zip';archive(source)
            output=root/'output';output.mkdir();(output/'keep').write_text('original')
            with self.assertRaisesRegex(ValueError,'must be absent'):
                recover(source,output)
            self.assertEqual((output/'keep').read_text(),'original')

    def test_reject_duplicate_zip_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.zip';archive(source)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(source,'a') as z:
                    z.writestr('decoded_c5/gui/gui_title.c5',synthetic_c5('gui_title'))
            with self.assertRaisesRegex(ValueError,'duplicate paths'):
                recover(source,root/'out')

    def test_reject_symlink_private_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.zip';archive(source)
            alias=root/'alias.zip';alias.symlink_to(source)
            with self.assertRaisesRegex(ValueError,'symlink'):
                recover(alias,root/'out')


if __name__=='__main__':
    unittest.main()
