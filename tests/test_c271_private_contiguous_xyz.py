"""C271 synthetic-only contiguous C5 XYZ provenance and native draw regressions."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from c271_private_contiguous_xyz import contiguous_source_xyz_proof, candidate_pair_contiguous
from test_c245_private_ordered_geometry_pair import fixture


def obj_xyz(obj):
    return [tuple(map(float, line.split()[1:4]))
            for line in obj.decode().splitlines() if line.startswith('v ')]


class C271ContiguousSourceTests(unittest.TestCase):
    def test_unique_full_source_order_and_native_pair(self):
        c5, obj = fixture()
        vx, ix, report = candidate_pair_contiguous(c5, obj, 2)
        self.assertEqual((report['mesh_count'], report['vertex_count'], report['triangle_count']), (2, 7, 3))
        self.assertEqual(report['source_contiguous_xyz_count'], 7)
        self.assertEqual(report['source_contiguous_xyz_stride'], 28)
        self.assertTrue(report['source_contiguous_xyz_order_exact_unique'])
        self.assertFalse(report['original_renderer_vertex_binding_verified'])
        self.assertFalse(report['asset_integrated_emulator_verified'])
        self.assertEqual(vx[:4], b'P3VX')
        self.assertEqual(ix[:4], b'P3IX')

    def test_actual_compiled_native_draw_probe_on_synthetic_pair(self):
        from c183_private_geometry_batch import build_probe
        c5, obj = fixture()
        vx, ix, _ = candidate_pair_contiguous(c5, obj, 2)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            a, b, exe = folder / 'p002.p3vx', folder / 'p002.p3ix', folder / 'probe'
            a.write_bytes(vx)
            b.write_bytes(ix)
            build_probe(exe)
            proc = subprocess.run([str(exe), str(a), str(b), '2', '3'],
                                  capture_output=True, text=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_permuted_obj_slots_rejected_even_if_global_multiset_matches(self):
        c5, obj = fixture()
        rows = obj.decode().splitlines()
        rows[0], rows[1] = rows[1], rows[0]
        with self.assertRaisesRegex(ValueError, 'no unique full contiguous'):
            candidate_pair_contiguous(c5, ('\n'.join(rows) + '\n').encode(), 2)

    def test_ambiguous_duplicate_full_sequence_rejected(self):
        c5, obj = fixture()
        source = c5[0xc8:0xc8 + 28 * 7]
        duplicate = c5 + source
        with self.assertRaisesRegex(ValueError, 'ambiguous full contiguous'):
            contiguous_source_xyz_proof(duplicate, obj_xyz(obj))

    def test_corrupt_source_record_rejected(self):
        c5, obj = fixture()
        data = bytearray(c5)
        data[0xc8 + 28 + 1] ^= 0x40
        with self.assertRaisesRegex(ValueError, 'no unique full contiguous'):
            contiguous_source_xyz_proof(bytes(data), obj_xyz(obj))

    def test_wrong_stride_and_short_source_rejected(self):
        c5, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'no unique full contiguous'):
            contiguous_source_xyz_proof(c5[0xc8:0xc8 + 7 * 12], obj_xyz(obj))
        with self.assertRaisesRegex(ValueError, 'invalid private C5'):
            contiguous_source_xyz_proof(b'', obj_xyz(obj))

    def test_invalid_and_out_of_range_coordinates_rejected(self):
        c5, obj = fixture()
        rows = obj_xyz(obj)
        rows[0] = (9.0, 0.5, 0.75)
        with self.assertRaisesRegex(ValueError, 'outside DS'):
            contiguous_source_xyz_proof(c5, rows)
        rows[0] = (float('nan'), 0.5, 0.75)
        with self.assertRaisesRegex(ValueError, 'invalid finite'):
            contiguous_source_xyz_proof(c5, rows)


if __name__ == '__main__':
    unittest.main()
