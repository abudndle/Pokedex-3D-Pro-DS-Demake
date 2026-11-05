"""C356: entirely synthetic original FSB relocation table tests."""
import struct
import tempfile
from pathlib import Path
import sys
import zipfile
import unittest
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c356_fsb_linkage_sites import linkage_record_table, recover

NAMES = ('Startup','change_lang','clocktest','page_album','page_ar3d','page_bg',
    'page_clock','page_dialog','page_kb','page_menu','page_message',
    'page_notification','page_photo','page_quiz','page_skill_search',
    'page_title','page_topmenu','page_uiload','page_viewer','page_viewer_init',
    'page_viewer_release','pageskill','pdb_loader','pdb_start','pokeselector')

def synthetic_fsb(stem, *, badsite=False, badorder=False, corruptlen=False,
                  duplicate=False):
    bytecode = b'\x12' * 124
    relocs = [(0x12345678,0xabcdef01,48),(0x456789ab,0,90)]
    if badsite: relocs[0] = (relocs[0][0],relocs[0][1],200)
    if badorder: relocs[0] = (relocs[0][0]+1,relocs[0][1],48)
    if duplicate: relocs[1] = (relocs[1][0],relocs[1][1],48)
    section = b''.join(struct.pack('<III', *r) for r in relocs)
    if corruptlen: section += b'\0'
    strings = (stem+'\0test\0sample\0TITLE_D\0BUTTON_M\0page_menu\0').encode()
    header = struct.pack('<8I',32,32+len(bytecode),
        32+len(bytecode)+len(section),32+len(bytecode)+len(section),
        32+len(bytecode)+len(section)+len(strings),0x4f588000,0,0)
    return header + bytecode + section + strings

def archive_fixture(path, *, mismatch=None, missing=None, duplicate=False):
    with zipfile.ZipFile(path,'w') as z:
        for language in ('romfs/scripts/','romfs/scripts_en/'):
            for stem in NAMES:
                path = language+stem+'.fsb'
                if path != missing:
                    z.writestr(path,synthetic_fsb(stem,badorder=path==mismatch))
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                z.writestr('romfs/scripts/page_title.fsb',synthetic_fsb('page_title'))

class C356SyntheticTests(unittest.TestCase):
    def test_linkage_offsets_and_opaque_hashes(self):
        info=linkage_record_table(synthetic_fsb('page_title'),'page_title')
        self.assertEqual(info['linkages'],2)
        self.assertEqual(info['source_linkages'][0]['linkage_key_a'],'12345678')
        self.assertEqual(info['source_linkages'][0]['code_site_offset'],48)
        self.assertEqual(info['source_linkages'][1]['compiled_relative_offset'],58)
        self.assertFalse(info['source_linkages'][0]['layout_coordinate_verified'])

    def test_reject_out_of_bounds_code_site(self):
        with self.assertRaisesRegex(ValueError,'site outside'):
            linkage_record_table(synthetic_fsb('page_title',badsite=True),'page_title')

    def test_reject_duplicate_patch_site(self):
        with self.assertRaisesRegex(ValueError,'duplicate FSB linkage'):
            linkage_record_table(synthetic_fsb('page_title',duplicate=True),'page_title')

    def test_reject_incomplete_linkage_record(self):
        with self.assertRaisesRegex(ValueError,'12-byte'):
            linkage_record_table(synthetic_fsb('page_title',corruptlen=True),'page_title')

    def test_all_25_original_script_pairs_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.zip';archive_fixture(p)
            r=recover(p)
            self.assertEqual(r['original_scripts_verified'],50)
            self.assertEqual(r['original_linkage_records'],100)
            self.assertEqual(r['original_linkages_per_language'],{'jp':50,'en':50})
            self.assertEqual(r['paired_language_scripts'],25)
            self.assertTrue(r['paired_linkage_identifiers_all_equal'])
            self.assertFalse(r['original_ui_coordinates_decoded'])
            self.assertFalse(r['release_ready'])

    def test_reject_jp_en_pair_linkage_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.zip'
            archive_fixture(p,mismatch='romfs/scripts_en/page_menu.fsb')
            with self.assertRaisesRegex(ValueError,'identities differ'):
                recover(p)

    def test_reject_missing_original_language_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.zip'
            archive_fixture(p,missing='romfs/scripts_en/page_title.fsb')
            with self.assertRaisesRegex(ValueError,'exactly 50'):
                recover(p)

    def test_reject_duplicate_original_source_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.zip';archive_fixture(p,duplicate=True)
            with self.assertRaisesRegex(ValueError,'duplicate'):
                recover(p)

    def test_reject_symlink_original_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.zip';archive_fixture(p)
            alias=Path(tmp)/'alias.zip';alias.symlink_to(p)
            with self.assertRaisesRegex(ValueError,'symlink'):
                recover(alias)

    def test_corrupted_compiled_section_header(self):
        invalid=bytearray(synthetic_fsb('page_title'))
        struct.pack_into('<I',invalid,8,5000)
        with self.assertRaisesRegex(ValueError,'header/section boundaries'):
            linkage_record_table(bytes(invalid),'page_title')

if __name__=='__main__':
    unittest.main()
