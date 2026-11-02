"""Synthetic C5 source descriptor-table boundary regressions."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c172_primitive_coverage_gate import verify_coverage
from c171_verified_primitive_gate import SCHEMA


def fixture():
    data = bytearray(276)
    data[:2] = b'\xc5\x78'
    struct.pack_into('<H', data, 0x10, 2)  # unrelated header field, NOT mesh count
    struct.pack_into('<HH', data, 0x14, 1, 1)
    struct.pack_into('<3I', data, 0x3c, 120, 140, 152)
    struct.pack_into('<5I', data, 120, 152, 0, 4 | (28 << 16), 0, 0)
    struct.pack_into('<3I', data, 140, 264, 0, 6 | (2 << 16))
    manifest = {'schema': SCHEMA, 'source': 'original-c5',
                'method': 'verified-original-primitive-order',
                'verified_by': 'source-decoder-crosscheck', 'model': 'p000',
                'meshes': [{'model': 'p000', 'mesh': 0,
                            'triangles': [[0, 1, 2], [1, 2, 3]]}]}
    return manifest, data


class DescriptorBounds(unittest.TestCase):
    def test_real_descriptor_counts_not_unrelated_header_field(self):
        manifest, source = fixture()
        self.assertEqual(verify_coverage(manifest, bytes(source))['verified_triangles'], 2)

    def test_mesh_outside_primary_secondary_tables_rejected(self):
        manifest, source = fixture()
        manifest['meshes'][0]['mesh'] = 1
        with self.assertRaisesRegex(ValueError, 'outside original descriptor'):
            verify_coverage(manifest, bytes(source))

    def test_invalid_descriptor_table_extent_rejected(self):
        manifest, source = fixture()
        struct.pack_into('<I', source, 0x40, 160)
        with self.assertRaisesRegex(ValueError, 'descriptor tables'):
            verify_coverage(manifest, bytes(source))

    def test_truncated_source_payload_rejected(self):
        manifest, source = fixture()
        with self.assertRaisesRegex(ValueError, 'primitive descriptor'):
            verify_coverage(manifest, bytes(source[:-2]))

    def test_non_c5_source_rejected(self):
        manifest, source = fixture()
        source[:2] = b'xx'
        with self.assertRaisesRegex(ValueError, 'C5 source header'):
            verify_coverage(manifest, bytes(source))


if __name__ == '__main__':
    unittest.main()
