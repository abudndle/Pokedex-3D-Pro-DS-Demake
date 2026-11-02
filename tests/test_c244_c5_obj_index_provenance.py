"""Synthetic-only C244 C5/OBJ byte-provenance regressions."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c244_c5_obj_index_provenance import verify


def fixture(pad=b'\x00\x00', duplicate=False):
    # Two C5 meshes: 3 vertices/1 triangle, 4 vertices/2 triangles.
    # First index payload is 6 bytes, requiring a 2-byte alignment gap.
    data = bytearray(0x220)
    data[:2] = b'\xc5\x78'
    struct.pack_into('<HH', data, 0x14, 2, 2)
    struct.pack_into('<3I', data, 0x3c, 0x80, 0xa8, 0xc0)
    struct.pack_into('<5I', data, 0x80, 0xc0, 0, (28 << 16) | 3, 0, 0)
    struct.pack_into('<5I', data, 0x94, 0x114, 0, (28 << 16) | 4, 0, 0)
    struct.pack_into('<3I', data, 0xa8, 0x184, 0, (2 << 16) | 3)
    struct.pack_into('<3I', data, 0xb4, 0x18c, 0, (2 << 16) | 6)
    data[0x184:0x198] = b'\xff' * (0x198 - 0x184)
    first = struct.pack('<3H', 0, 1, 2)
    second = struct.pack('<6H', 0, 1, 2, 0, 2, 3)
    stream = first + pad + second
    data[0x1a0:0x1a0 + len(stream)] = stream
    if duplicate:
        data[0x1c0:0x1c0 + len(stream)] = stream
    obj = '\n'.join(['v 0 0 0'] * 7 +
                    ['f 1 2 3', 'f 4 5 6', 'f 4 6 7'])
    return bytes(data), obj


class C244ProvenanceTests(unittest.TestCase):
    def test_exact_two_meshes(self):
        c5, obj = fixture()
        r = verify(c5, obj)
        self.assertTrue(r['source_face_bytes_exact_and_unique'])
        self.assertEqual((r['mesh_count'], r['triangle_count']), (2, 3))
        self.assertFalse(r['original_renderer_primitive_binding_verified'])

    def test_nonzero_inter_mesh_padding_accepted(self):
        c5, obj = fixture(pad=b'\x85\x3d')
        self.assertEqual(verify(c5, obj)['nonzero_alignment_gaps'], 1)

    def test_wrong_triangle_rejected(self):
        c5, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'no unique'):
            verify(c5, obj.replace('f 4 6 7', 'f 4 7 6'))

    def test_duplicate_source_region_rejected(self):
        c5, obj = fixture(duplicate=True)
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            verify(c5, obj)

    def test_cross_mesh_face_rejected(self):
        c5, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'crosses C5 mesh'):
            verify(c5, obj.replace('f 4 5 6', 'f 3 5 6'))

    def test_bad_descriptor_count_rejected(self):
        c5, obj = fixture()
        b = bytearray(c5)
        struct.pack_into('<H', b, 0x16, 3)
        with self.assertRaisesRegex(ValueError, 'descriptor bounds'):
            verify(bytes(b), obj)

    def test_invalid_obj_face_rejected(self):
        c5, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'outside vertex'):
            verify(c5, obj.replace('f 4 6 7', 'f 4 6 8'))

    def test_unsafe_source_type_rejected(self):
        _, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'invalid C5'):
            verify(bytearray(128), obj)


if __name__ == '__main__':
    unittest.main()
