"""C245 synthetic-only source-ordered native geometry pair regressions."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from c245_private_ordered_geometry_pair import build_pair, pack_index_stream, stage_private


def fixture(shift=8, duplicate_faces=False):
    # 2 source meshes, 7 distinct vertices, 3 source triangles, 28-byte stride.
    vertices = [
        (0.25, 0.5, 0.75), (1.0, 0.5, 0.25), (0.25, 1.0, 0.5),
        (-0.25, 0.25, 0.5), (0.5, -0.5, 0.75), (0.75, 0.25, -0.25),
        (1.0, 0.75, -0.5),
    ]
    data = bytearray(0x220)
    data[:2] = b'\xc5\x78'
    struct.pack_into('<HH', data, 0x14, 2, 2)
    struct.pack_into('<3I', data, 0x3c, 0x80, 0xa8, 0xc0)
    struct.pack_into('<5I', data, 0x80, 0xc0, 0, (28 << 16) | 3, 0, 0)
    struct.pack_into('<5I', data, 0x94, 0x114, 0, (28 << 16) | 4, 0, 0)
    struct.pack_into('<3I', data, 0xa8, 0x184, 0, (2 << 16) | 3)
    struct.pack_into('<3I', data, 0xb4, 0x18c, 0, (2 << 16) | 6)
    for base, group in ((0xc0, vertices[:3]), (0x114, vertices[3:])):
        for j, row in enumerate(group):
            start = base + j * 28
            data[start:start + 28] = b'\xff' * 28
            data[start + shift:start + shift + 12] = struct.pack('<3f', *row)
    data[0x184:0x198] = b'\xff' * 20
    face_bytes = struct.pack('<3H', 0, 1, 2) + b'\x00\x00' + struct.pack('<6H', 0, 1, 2, 0, 2, 3)
    data[0x1a0:0x1a0 + len(face_bytes)] = face_bytes
    if duplicate_faces:
        data[0x1c0:0x1c0 + len(face_bytes)] = face_bytes
    obj = ('\n'.join('v %s %s %s' % v for v in vertices) + '\n' +
           'f 1 2 3\nf 4 5 6\nf 4 6 7\n').encode()
    return bytes(data), obj


class C245OrderedGeometryTests(unittest.TestCase):
    def test_full_two_mesh_native_pair(self):
        c5, obj = fixture()
        vx, ix, result = build_pair(c5, obj, 2)
        self.assertEqual((result['mesh_count'], result['vertex_count'], result['triangle_count']), (2, 7, 3))
        self.assertTrue(result['source_c5_xyz_order_exact'])
        self.assertTrue(result['source_c5_face_bytes_exact_unique'])
        self.assertFalse(result['original_3ds_renderer_binding_verified'])
        self.assertFalse(result['private_asset_emulator_verified'])
        self.assertEqual(struct.unpack_from('<4sHHH', ix), (b'P3IX', 1, 2, 2))
        self.assertEqual(struct.unpack_from('<4sHHHH', vx), (b'P3VX', 1, 2, 2, 0))

    def test_real_native_c_gl_draw_accepts_synthetic_pair(self):
        from c183_private_geometry_batch import build_probe
        c5, obj = fixture()
        vx, ix, _ = build_pair(c5, obj, 2)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            exe = folder / 'probe'
            a, b = folder / 'p002.p3vx', folder / 'p002.p3ix'
            a.write_bytes(vx)
            b.write_bytes(ix)
            build_probe(exe)
            run = subprocess.run([str(exe), str(a), str(b), '2', '3'],
                                 capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_multiset_match_does_not_allow_vertex_permutation(self):
        c5, obj = fixture()
        rows = obj.decode().splitlines()
        rows[0], rows[1] = rows[1], rows[0]
        with self.assertRaisesRegex(ValueError, 'vertex order differs'):
            build_pair(c5, ('\n'.join(rows) + '\n').encode(), 2)

    def test_wrong_original_index_bytes_rejected(self):
        c5, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'no unique aligned'):
            build_pair(c5, obj.replace(b'f 4 6 7', b'f 4 7 6'), 2)

    def test_ambiguous_original_face_region_rejected(self):
        c5, obj = fixture(duplicate_faces=True)
        with self.assertRaisesRegex(ValueError, 'ambiguous C5'):
            build_pair(c5, obj, 2)

    def test_native_triangle_budget_rejected(self):
        with self.assertRaisesRegex(ValueError, 'native DS geometry budget'):
            pack_index_stream([3], [1801 * 3], [(0, 1, 2)] * 1801, 2)

    def test_mesh_partition_rejected(self):
        with self.assertRaisesRegex(ValueError, 'crosses descriptor'):
            pack_index_stream([3, 4], [3, 3], [(0, 1, 2), (2, 3, 4)], 2)

    def test_source_coordinate_overflow_rejected(self):
        c5, obj = fixture()
        c5 = bytearray(c5)
        struct.pack_into('<f', c5, 0xc0 + 8, 9.0)
        obj = obj.replace(b'v 0.25 0.5 0.75', b'v 9.0 0.5 0.75')
        with self.assertRaisesRegex(ValueError, 'outside DS'):
            build_pair(bytes(c5), obj, 2)

    def test_private_output_atomic_and_permissions(self):
        c5, obj = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            c5_path, obj_path = folder / 'p002.c5', folder / 'p002.obj'
            c5_path.write_bytes(c5)
            obj_path.write_bytes(obj)
            output = folder / 'p002-pair'
            result = stage_private(c5_path, obj_path, output)
            self.assertEqual(result['triangle_count'], 3)
            self.assertEqual({x.name for x in output.iterdir()}, {'p002.p3vx', 'p002.p3ix', 'p002.json'})
            for path in output.iterdir():
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            with self.assertRaisesRegex(ValueError, 'must not exist'):
                stage_private(c5_path, obj_path, output)

    def test_no_output_if_source_mismatch(self):
        c5, obj = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            c5_path, obj_path = folder / 'p002.c5', folder / 'p002.obj'
            c5_path.write_bytes(c5)
            obj_path.write_bytes(obj.replace(b'f 4 6 7', b'f 4 7 6'))
            output = folder / 'p002-pair'
            with self.assertRaises(ValueError):
                stage_private(c5_path, obj_path, output)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
