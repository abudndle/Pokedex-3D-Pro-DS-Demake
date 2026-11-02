"""Synthetic-only tests; no Nintendo data, model hashes or ROMs."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('c211', ROOT/'tools/c211_private_source_pair.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def pair(mesh=2, indices=((0, 1, 2), (1, 2, 3)), vertices=4, model=0):
    table = struct.pack('<HHI', mesh, vertices, 0)
    payload = b'\0' * (vertices * 6)
    vx = struct.pack('<4sHHHHI', b'P3VX', 1, model, 1, 0,
                     zlib.crc32(table + payload) & 0xffffffff) + table + payload
    ix = struct.pack('<4sHHH', b'P3IX', 1, model, 1)
    ix += struct.pack('<HI', mesh, len(indices))
    ix += b''.join(struct.pack('<3H', *tri) for tri in indices)
    return vx, ix


class PairGateTests(unittest.TestCase):
    def test_valid_native_pair_is_not_claimed_as_full_original(self):
        result = mod.validate_native_pair(*pair(), 0)
        self.assertEqual((result['vertices'], result['triangles']), (4, 2))
        self.assertFalse(result['complete_original_model_verified'])
        self.assertFalse(result['private_asset_emulator_verified'])

    def test_crc_corruption(self):
        vx, ix = pair()
        with self.assertRaisesRegex(ValueError, 'CRC'):
            mod.validate_native_pair(vx[:-1] + b'\1', ix, 0)

    def test_source_mesh_mismatch(self):
        vx, ix = pair(mesh=2)
        ix = bytearray(ix)
        struct.pack_into('<H', ix, 10, 3)
        with self.assertRaisesRegex(ValueError, 'mesh mismatch'):
            mod.validate_native_pair(vx, ix, 0)

    def test_index_outside_source_mesh(self):
        with self.assertRaisesRegex(ValueError, 'vertex ownership'):
            mod.validate_native_pair(*pair(indices=((0, 1, 4),)), 0)

    def test_degenerate_triangle(self):
        with self.assertRaisesRegex(ValueError, 'vertex ownership'):
            mod.validate_native_pair(*pair(indices=((0, 1, 1),)), 0)

    def test_native_triangle_budget(self):
        with self.assertRaisesRegex(ValueError, 'triangle budget'):
            mod.validate_native_pair(*pair(indices=((0, 1, 2),) * 1801), 0)

    def test_wrong_model(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            mod.validate_native_pair(*pair(), 1)

    def test_trailing_index_bytes(self):
        vx, ix = pair()
        with self.assertRaisesRegex(ValueError, 'trailing'):
            mod.validate_native_pair(vx, ix + b'\0', 0)

    def test_bad_packed_vertex_table(self):
        vx, ix = pair()
        vx = bytearray(vx)
        struct.pack_into('<I', vx, 20, 1)
        struct.pack_into('<I', vx, 12, zlib.crc32(vx[16:]) & 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'mesh descriptor'):
            mod.validate_native_pair(bytes(vx), ix, 0)

    @unittest.skipUnless((ROOT/'tools/c207_private_c5_xyz.py').exists(),
                         'full source converter modules are available in GitHub checkout')
    def test_independent_original_xyz_and_topology_exporters(self):
        sys.path.insert(0, str(ROOT/'tools'))
        from c207_private_c5_xyz import convert
        from c173_verified_primitive_export import export
        from c171_verified_primitive_gate import SCHEMA
        xyz = ((0.25, 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
        a, b, c = 0x78, 0x8c, 0x98
        source = bytearray(c)
        source[:2] = b'\xc5\x78'
        struct.pack_into('<H', source, 0x10, 1)
        struct.pack_into('<HH', source, 0x14, 1, 1)
        struct.pack_into('<3I', source, 0x3c, a, b, c)
        struct.pack_into('<5I', source, a, c, 0, 4 | (28 << 16), 0, 0)
        struct.pack_into('<3I', source, b, c, 0, 6 | (2 << 16))
        for row in xyz:
            source.extend(struct.pack('<3f', *row) + bytes(16))
        reference = ('\n'.join('v %s %s %s' % row for row in xyz)+'\n').encode()
        manifest = {'schema': SCHEMA, 'source': 'original-c5',
                    'method': 'verified-original-primitive-order',
                    'verified_by': 'source-decoder-crosscheck', 'model': 'p000',
                    'meshes': [{'model': 'p000', 'mesh': 0,
                                'triangles': [[0, 1, 2], [1, 2, 3]]}]}
        vx = convert(bytes(source), reference, 0)[1]
        ix = export(manifest, bytes(source))
        result = mod.validate_source_pair(bytes(source), reference, manifest, vx, ix, 0)
        self.assertEqual((result['vertices'], result['triangles']), (4, 2))
        self.assertTrue(result['source_triangle_manifest_verified'])
        self.assertFalse(result['complete_original_model_verified'])
        modified = bytearray(ix)
        modified[-1], modified[-3] = modified[-3], modified[-1]
        with self.assertRaisesRegex(ValueError, 'verified original primitive map'):
            mod.validate_source_pair(bytes(source), reference, manifest, vx, bytes(modified), 0)

    def test_invalid_model_roster_hole(self):
        with self.assertRaisesRegex(ValueError, 'model identity'):
            mod.validate_native_pair(*pair(model=721), 721)


if __name__ == '__main__':
    unittest.main()
