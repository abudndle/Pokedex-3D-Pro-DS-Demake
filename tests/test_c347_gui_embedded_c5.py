"""C347 synthetic-only nested GUI C5 extraction tests."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c347_gui_embedded_c5 import read_container, extract, EXPECTED


def fixture(inner=b'\xc5\x78\x00\x02' + bytes(116)):
    data = bytearray(0x90 + len(inner) + 4)
    data[:4] = b'\xc5\x78\x00\x01'
    struct.pack_into('<I', data, 0x68, 0x90)
    data[0x90:0x90 + len(inner)] = inner
    struct.pack_into('<I', data, 0x94, len(inner))
    return bytes(data)


class C347Tests(unittest.TestCase):
    def test_valid_nested_bounds(self):
        pos, inner = read_container(fixture())
        self.assertEqual(pos, 0x90)
        self.assertEqual(inner[:4], b'\xc5\x78\x00\x02')
        self.assertEqual(len(inner), 120)

    def test_reject_invalid_inner_span(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 0x94, 999999)
        with self.assertRaisesRegex(ValueError, 'length invalid'):
            read_container(bytes(data))

    def test_reject_invalid_inner_magic(self):
        data = bytearray(fixture())
        data[0x90] = 0
        with self.assertRaisesRegex(ValueError, 'nested C5 header'):
            read_container(bytes(data))

    def test_complete_private_staging_and_no_release_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'synthetic.zip'
            with zipfile.ZipFile(source, 'w') as z:
                for base in EXPECTED:
                    z.writestr(f'decoded_c5/gui/{base}.c5', fixture())
            dest = root / 'private'
            report = extract(source, dest)
            self.assertEqual(report['nested_source_count'], 16)
            self.assertFalse(report['original_texture_pixels_decoded'])
            self.assertFalse(report['original_release_ready'])
            self.assertEqual(len(list(dest.rglob('*.embedded.c5'))), 16)
            with self.assertRaisesRegex(ValueError, 'exists'):
                extract(source, dest)

    def test_missing_source_is_atomic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'synthetic.zip'
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('decoded_c5/gui/gui_title.c5', fixture())
            dest = root / 'private'
            with self.assertRaisesRegex(ValueError, 'missing source'):
                extract(source, dest)
            self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()
