import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from c173_verified_primitive_export import export
from c171_verified_primitive_gate import SCHEMA


def fixture(triangle_count=2):
    source = bytearray(224)
    source[:2] = bytes((0xc5, 0x78))
    struct.pack_into('<H', source, 0x10, 1)
    struct.pack_into('<2I', source, 0x3c, 120, 140)
    struct.pack_into('<5I', source, 120, 0, 0, 4, 0, 0)
    struct.pack_into('<3I', source, 140, 200, 0, triangle_count * 3)
    manifest = {'schema': SCHEMA, 'source': 'original-c5',
                'method': 'verified-original-primitive-order',
                'verified_by': 'source-decoder-crosscheck', 'model': 'p000',
                'meshes': [{'model': 'p000', 'mesh': 0,
                            'triangles': [[0, 1, 2]] * triangle_count}]}
    return manifest, bytes(source)


class ExportLimits(unittest.TestCase):
    def test_valid_native_export(self):
        manifest, source = fixture(2)
        raw = export(manifest, source)
        self.assertEqual(struct.unpack_from('<4sHHH', raw), (b'P3IX', 1, 0, 1))
        self.assertEqual(struct.unpack_from('<HI', raw, 10), (0, 2))

    def test_1800_triangle_boundary_accepted(self):
        manifest, source = fixture(1800)
        self.assertEqual(len(export(manifest, source)), 16 + 1800 * 6)

    def test_1801_triangle_overflow_rejected(self):
        manifest, source = fixture(1801)
        with self.assertRaisesRegex(ValueError, 'triangle budget'):
            export(manifest, source)

    def test_incomplete_original_source_count_rejected(self):
        manifest, source = fixture(2)
        manifest['meshes'][0]['triangles'].pop()
        with self.assertRaises(ValueError):
            export(manifest, source)


if __name__ == '__main__':
    unittest.main()
