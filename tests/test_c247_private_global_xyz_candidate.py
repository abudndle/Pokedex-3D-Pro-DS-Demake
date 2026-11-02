"""C247 synthetic-only global C5 XYZ candidate and native draw regressions."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from c247_private_global_xyz_candidate import candidate_pair, global_xyz_source_proof, stage_private
from test_c245_private_ordered_geometry_pair import fixture


def xyz_rows(obj):
    return [tuple(map(float, line.split()[1:])) for line in obj.decode().splitlines()
            if line.startswith('v ')]


class C247CandidateTests(unittest.TestCase):
    def test_unique_global_xyz_and_native_pair(self):
        c5, obj = fixture()
        vx, ix, report = candidate_pair(c5, obj, 2)
        self.assertEqual((report['mesh_count'], report['vertex_count'], report['triangle_count']), (2, 7, 3))
        self.assertEqual(report['source_xyz_alignment_residue_private'], 4)
        self.assertTrue(report['original_c5_face_bytes_exact_unique'])
        self.assertFalse(report['original_3ds_vertex_slot_binding_verified'])
        self.assertFalse(report['asset_integrated_emulator_verified'])
        self.assertEqual(vx[:4], b'P3VX')
        self.assertEqual(ix[:4], b'P3IX')

    def test_native_compiled_gl_adapter_accepts_candidate(self):
        from c183_private_geometry_batch import build_probe
        c5, obj = fixture()
        vx, ix, _ = candidate_pair(c5, obj, 2)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            probe = folder / 'probe'
            a, b = folder / 'p002.p3vx', folder / 'p002.p3ix'
            a.write_bytes(vx)
            b.write_bytes(ix)
            build_probe(probe)
            proc = subprocess.run([str(probe), str(a), str(b), '2', '3'],
                                  capture_output=True, text=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_permuted_reference_is_candidate_not_original_renderer_proof(self):
        c5, obj = fixture()
        rows = obj.decode().splitlines()
        rows[0], rows[1] = rows[1], rows[0]
        _, _, report = candidate_pair(c5, ('\n'.join(rows) + '\n').encode(), 2)
        self.assertFalse(report['original_3ds_vertex_slot_binding_verified'])

    def test_wrong_original_face_bytes_rejected(self):
        c5, obj = fixture()
        with self.assertRaisesRegex(ValueError, 'no unique aligned'):
            candidate_pair(c5, obj.replace(b'f 4 6 7', b'f 4 7 6'), 2)

    def test_missing_original_xyz_rejected(self):
        c5, obj = fixture()
        rows = xyz_rows(obj)
        rows[0] = (7.0, 7.0, 7.0)
        with self.assertRaisesRegex(ValueError, 'source XYZ stride residue'):
            global_xyz_source_proof(c5, rows)

    def test_ambiguous_global_stride_residue_rejected(self):
        rows = [(0.25, 0.5, 0.75), (1.0, 0.5, 0.25), (0.25, 1.0, 0.5)]
        data = bytearray(256)
        for i, xyz in enumerate(rows):
            packed = struct.pack('<3f', *xyz)
            data[i * 28:i * 28 + 12] = packed
            data[i * 28 + 16:i * 28 + 28] = packed
        with self.assertRaisesRegex(ValueError, 'found 2'):
            global_xyz_source_proof(bytes(data), rows)

    def test_duplicate_xyz_multiplicity_rejected(self):
        rows = [(0.25, 0.5, 0.75)] * 3
        data = bytearray(200)
        data[:12] = struct.pack('<3f', *rows[0])
        with self.assertRaisesRegex(ValueError, 'source XYZ stride residue'):
            global_xyz_source_proof(bytes(data), rows)

    def test_ds_quantization_overflow_rejected(self):
        c5, obj = fixture()
        rows = xyz_rows(obj)
        rows[0] = (9.0, 0.0, 0.0)
        with self.assertRaisesRegex(ValueError, 'outside signed DS'):
            global_xyz_source_proof(c5, rows)

    def test_private_atomic_staging_and_no_overwrite(self):
        c5, obj = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            a, b = folder / 'p002.c5', folder / 'p002.obj'
            a.write_bytes(c5)
            b.write_bytes(obj)
            target = folder / 'candidate'
            report = stage_private(a, b, target)
            self.assertFalse(report['full_original_model_verified'])
            self.assertEqual({x.name for x in target.iterdir()}, {'p002.p3vx', 'p002.p3ix', 'p002.json'})
            for item in target.iterdir():
                self.assertEqual(item.stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(ValueError, 'must not exist'):
                stage_private(a, b, target)


if __name__ == '__main__':
    unittest.main()
