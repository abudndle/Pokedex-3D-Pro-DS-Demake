"""C355 asset-free synthetic FSB catalog tests."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from c355_fsb_ui_symbols import parse_fsb, audit

NAMES=('Startup','change_lang','clocktest','page_album','page_ar3d','page_bg',
       'page_clock','page_dialog','page_kb','page_menu','page_message',
       'page_notification','page_photo','page_quiz','page_skill_search',
       'page_title','page_topmenu','page_uiload','page_viewer',
       'page_viewer_init','page_viewer_release','pageskill',
       'pdb_loader','pdb_start','pokeselector')


def fixture(name, *, utf8=True, double_nul=False):
    vals=(name.lower() if name=='Startup' else name, 'page_menu',
          'page_viewer', 'TouchListM', 'BUTTON_M', 'source-name')
    if not utf8:
        pool=b'\xff'+b'\0'.join(v.encode('utf8') for v in vals[1:])+b'\0'
    else:
        pool=b'\0'.join(v.encode('utf8') for v in vals)+b'\0'
    if double_nul:
        pool+=b'\0'
    head=struct.pack('<8I',32,80,92,92,92+len(pool),0x4f588000,0,0)
    return head+b'\x11'*48+b'\x22'*12+pool


def source_zip(path, *, missing=None, duplicate=False, unsafe=False):
    with zipfile.ZipFile(path,'w') as z:
        for scope in ('romfs/scripts/','romfs/scripts_en/'):
            for name in NAMES:
                full=scope+name+'.fsb'
                if full!=missing:
                    z.writestr(full, fixture(name))
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                z.writestr('romfs/scripts/page_title.fsb', fixture('page_title'))
        if unsafe:
            z.writestr('../outside',b'bad')


class C355SyntheticTests(unittest.TestCase):
    def test_exact_utf8_pool_offsets_and_hashes(self):
        raw=fixture('page_title')
        d=parse_fsb(raw,'page_title')
        self.assertEqual(d['original_string_section']['start'],92)
        self.assertEqual(d['strings'][0]['utf8'],'page_title')
        self.assertEqual(d['strings'][0]['source_offset'],92)
        self.assertEqual(d['strings'][0]['source_sha256'],hashlib.sha256(b'page_title').hexdigest())
        self.assertEqual(d['compiled_section']['sha256'],hashlib.sha256(b'\x11'*48).hexdigest())

    def test_source_records_may_contain_empty_pool_separators(self):
        d=parse_fsb(fixture('page_title',double_nul=True),'page_title')
        self.assertEqual(len(d['strings']),6)

    def test_50_script_pair_audit_uses_strings_not_runtime_assumptions(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'input.zip';source_zip(src)
            r=audit(src)
            self.assertEqual(r['original_scripts_verified'],50)
            self.assertEqual(r['original_scripts_per_language'],{'en':25,'jp':25})
            self.assertEqual(r['original_source_string_records'],300)
            self.assertTrue(r['literal_script_reference_candidates']>0)
            self.assertTrue(r['ui_name_or_touch_label_candidates']>0)
            self.assertFalse(r['source_script_refs_are_runtime_control_flow'])
            self.assertFalse(r['source_text_labels_are_touch_rectangles'])
            self.assertFalse(r['original_layout_coordinates_decoded'])
            self.assertFalse(r['release_ready'])

    def test_reject_truncated_fsb_header(self):
        with self.assertRaisesRegex(ValueError,'safety limits'):
            parse_fsb(b'x'*12,'page_title')

    def test_reject_corrupted_string_boundary(self):
        raw=bytearray(fixture('page_title'))
        struct.pack_into('<I',raw,12,93)
        with self.assertRaises(ValueError):
            parse_fsb(bytes(raw),'page_title')

    def test_reject_invalid_utf8(self):
        with self.assertRaisesRegex(ValueError,'UTF-8'):
            parse_fsb(fixture('page_title',utf8=False),'page_title')

    def test_reject_duplicate_member(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'source.zip';source_zip(src,duplicate=True)
            with self.assertRaisesRegex(ValueError,'duplicate'):
                audit(src)

    def test_reject_missing_japanese_script(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'source.zip'
            source_zip(src,missing='romfs/scripts/page_album.fsb')
            with self.assertRaisesRegex(ValueError,'exactly 50'):
                audit(src)

    def test_reject_zip_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'source.zip';source_zip(src,unsafe=True)
            with self.assertRaisesRegex(ValueError,'unsafe'):
                audit(src)

    def test_reject_symlink_original_archive(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'src.zip';source_zip(src)
            alias=Path(td)/'link.zip';alias.symlink_to(src)
            with self.assertRaisesRegex(ValueError,'symlink'):
                audit(alias)


if __name__=='__main__':
    unittest.main()
