"""C346 synthetic GUI C5 inventory regressions; no Nintendo assets."""
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c346_gui_c5_inventory import EXPECTED, inventory


class C346Tests(unittest.TestCase):
    def fixture(self, path, corrupt=None, omit=None):
        with zipfile.ZipFile(path, 'w') as z:
            for name in EXPECTED:
                for p, data in ((f'romfs/gui/{name}.z5', b'\x40hello'),
                                (f'decoded_c5/gui/{name}.c5', b'\xc5\x78\x00\x01' + bytes(116))):
                    if p != omit:
                        z.writestr(p, b'notc5' if p == corrupt else data)

    def test_valid_pairs(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'sources.zip'
            self.fixture(source)
            report = inventory(source)
            self.assertEqual(report['verified_gui_resource_pairs'], 16)
            self.assertEqual(len(report['resources']), 16)
            self.assertFalse(report['original_release_ready'])
            self.assertFalse(report['actual_texture_pixels_decoded'])

    def test_missing_pair(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'sources.zip'
            self.fixture(source, omit='decoded_c5/gui/gui_title.c5')
            with self.assertRaisesRegex(ValueError, 'missing matched'):
                inventory(source)

    def test_corrupt_c5(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'sources.zip'
            self.fixture(source, corrupt='decoded_c5/gui/gui_title.c5')
            with self.assertRaisesRegex(ValueError, 'unsupported original C5'):
                inventory(source)

    def test_zip_traversal(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'sources.zip'
            self.fixture(source)
            with zipfile.ZipFile(source, 'a') as z:
                z.writestr('../outside', b'no')
            with self.assertRaisesRegex(ValueError, 'unsafe source archive path'):
                inventory(source)

    def test_bad_section_offset(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'sources.zip'
            with zipfile.ZipFile(source, 'w') as z:
                for name in EXPECTED:
                    z.writestr(f'romfs/gui/{name}.z5', b'\x40test')
                    data = bytearray(b'\xc5\x78\x00\x01' + bytes(116))
                    if name == 'gui_title':
                        data[0x2c:0x30] = (99999).to_bytes(4, 'little')
                    z.writestr(f'decoded_c5/gui/{name}.c5', data)
            with self.assertRaisesRegex(ValueError, 'offset outside'):
                inventory(source)


if __name__ == '__main__':
    unittest.main()
