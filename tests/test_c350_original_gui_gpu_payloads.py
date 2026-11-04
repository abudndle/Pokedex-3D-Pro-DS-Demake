"""C350 security and byte-integrity tests: SYNTHETIC resources only."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c350_original_gui_gpu_payloads import EXPECTED, recover, split_gpu_container


def fixture(key, mismatch=False):
    raw = bytearray(0x78 + 0x100)
    raw[:4] = b'\xc5\x78\x00\x01'
    struct.pack_into('<II', raw, 4, 0x100, 0x100)
    struct.pack_into('<I', raw, 0x68, 0x80)
    raw[0x80:0x84] = b'\xc5\x78\x00\x02'
    struct.pack_into('<I', raw, 0x84, 0x78)
    stem = key.split('/')[-1]
    color = (23 + int(stem[-2:])) if stem[-2:].isdigit() else {
        'gui_title': 71, 'gui_common': 91,
        'en/gui_title': 51, 'jp/gui_title': 52}[key]
    if key.startswith('jp/') and mismatch and stem == 'gui01':
        color ^= 15
    return bytes(raw) + bytes([color]) * 0x100


def source_zip(dest, *, missing=None, mismatch=False, duplicate=False):
    with zipfile.ZipFile(dest, 'w') as z:
        for key in EXPECTED:
            name = f'decoded_c5/gui/{key}.c5'
            if name == missing:
                continue
            z.writestr(name, fixture(key, mismatch=mismatch))
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr('decoded_c5/gui/gui_title.c5', fixture('gui_title'))


class C350PrivateGPUSecurityTests(unittest.TestCase):
    def test_extract_16_sources_deduplicates_10_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            source_zip(archive)
            report = recover(archive, root / 'stage')
            self.assertEqual(report['source_gui_c5_files'], 16)
            self.assertEqual(report['unique_original_gpu_blobs'], 10)
            self.assertEqual(report['en_jp_numbered_gui_gpu_pairs_identical'], 6)
            self.assertFalse(report['ds_ui_screen_bitmaps_ready'])
            self.assertFalse(report['original_texture_pixel_formats_decoded'])
            self.assertEqual(len(list((root / 'stage/gpu').glob('*.bin'))), 10)
            loaded = json.loads((root / 'stage/C350_PRIVATE_GPU_SOURCES.json').read_text())
            self.assertEqual(loaded['entries'], report['entries'])

    def test_reject_boundary_mismatch(self):
        corrupted = bytearray(fixture('en/gui01'))
        struct.pack_into('<I', corrupted, 8, 0x200)
        with self.assertRaisesRegex(ValueError, 'boundary'):
            split_gpu_container(bytes(corrupted))

    def test_reject_cross_language_mismatch_atomically(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            source_zip(archive, mismatch=True)
            with self.assertRaisesRegex(ValueError, 'GPU source mismatch'):
                recover(archive, root / 'stage')
            self.assertFalse((root / 'stage').exists())

    def test_reject_missing_source_atomically(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            source_zip(archive, missing='decoded_c5/gui/en/gui05.c5')
            with self.assertRaisesRegex(ValueError, 'missing original'):
                recover(archive, root / 'stage')
            self.assertFalse((root / 'stage').exists())

    def test_reject_duplicate_zip_member(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            source_zip(archive, duplicate=True)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                recover(archive, root / 'stage')

    def test_reject_inner_metadata_overlapping_gpu(self):
        corrupted = bytearray(fixture('gui_title'))
        struct.pack_into('<I', corrupted, 0x84, 0x100)
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            split_gpu_container(bytes(corrupted))

    def test_reject_existing_private_output_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            source_zip(archive)
            dest = root / 'stage'; dest.mkdir()
            (dest / 'keep').write_text('original')
            with self.assertRaisesRegex(ValueError, 'must not exist'):
                recover(archive, dest)
            self.assertEqual((dest / 'keep').read_text(), 'original')

    def test_reject_symlink_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            source_zip(archive)
            alias = root / 'link.zip'; alias.symlink_to(archive)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                recover(alias, root / 'stage')


if __name__ == '__main__':
    unittest.main()
