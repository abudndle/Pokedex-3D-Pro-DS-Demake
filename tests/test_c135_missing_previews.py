"""C135: source-only regression; all geometry and archives are synthetic."""
import csv
import io
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import importlib.util

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from c135_recover_missing_previews import (
    build_ds3m_v2, combine_private_nitrofs, read_c56_reference,
    _validate_c86_missing, MISSING, NEUTRAL_RGB,
)


def quad():
    return [[(0., 0., 0.), (1., 0., 0.), (1., 1., 0.), (0., 1., 0.)]], [
        [(0, 1, 2), (0, 2, 3)]]


def synthetic_c5():
    """One quad, with separate C5 descriptor headers, vertices, u16 faces."""
    raw = bytearray(0x160)
    raw[0:2] = b'\xc5\x78'
    struct.pack_into('<H', raw, 0x14, 1)
    struct.pack_into('<H', raw, 0x16, 1)
    for p, value in ((0x3c, 0x78), (0x40, 0x8c), (0x44, 0x98),
                     (0x48, 0x98), (0x4c, 0x98)):
        struct.pack_into('<I', raw, p, value)
    struct.pack_into('<5I', raw, 0x78, 0x100, 0, (20 << 16) | 4, 0, 0)
    struct.pack_into('<3I', raw, 0x8c, 0x150, 0, (2 << 16) | 6)
    for i, xyz in enumerate(quad()[0][0]):
        struct.pack_into('<3f', raw, 0x100 + 20 * i, *xyz)
    struct.pack_into('<6H', raw, 0x150, 0, 1, 2, 0, 2, 3)
    return bytes(raw)


class C135Tests(unittest.TestCase):
    def test_original_face_only_ds3m_v2_transport(self):
        vertices, groups = quad()
        blob, report = build_ds3m_v2(vertices, groups)
        magic, version, n, nvert, source_faces = struct.unpack_from('<4sHHII', blob)
        self.assertEqual((magic, version, n, nvert, source_faces),
                         (b'DS3M', 2, 2, 4, 2))
        self.assertEqual(len(blob), 16 + 21 * n)
        self.assertEqual(blob[-3*n:], NEUTRAL_RGB * n)
        self.assertEqual(report['source_meshes_sampled'], 1)
        self.assertFalse(report['materials_verified'])
        self.assertFalse(report['uv_verified'])

    def test_reject_degenerate_nonfinite_and_unsupported_source(self):
        vertices, groups = quad()
        for faces in ([(0, 0, 1)], [(0, 1, 4)], [(0, 1)], [(0, 1, 2, 3)]):
            with self.assertRaises(ValueError):
                build_ds3m_v2(vertices, [faces])
        for changed in ((float('nan'), 0, 0), (1000., 0, 0)):
            bad = [list(vertices[0])]
            bad[0][0] = changed
            with self.assertRaises(ValueError):
                build_ds3m_v2(bad, groups)
        with self.assertRaises(ValueError):
            build_ds3m_v2(vertices, groups, limit=0)
        with self.assertRaises(ValueError):
            build_ds3m_v2(vertices * 601, groups * 601)

    def test_quota_sampling_keeps_each_original_source_mesh(self):
        vertices, groups = quad()
        v = vertices * 3
        g = groups * 3
        blob, report = build_ds3m_v2(v, g, limit=3)
        self.assertEqual(report['source_meshes_sampled'], 3)
        self.assertEqual(report['preview_triangles'], 3)
        self.assertEqual(struct.unpack_from('<H', blob, 6)[0], 3)

    def test_model_coverage_needs_exact_four_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'c86.json'
            report = {'per_model': [
                {'model_id': f'p{n:03d}', 'fallback_preview': n not in MISSING}
                for n in range(734) if n not in (721, 722, 723, 724)]}
            path.write_text(json.dumps(report))
            _validate_c86_missing(path)
            report['per_model'][-1]['fallback_preview'] = True
            path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, 'missing model list'):
                _validate_c86_missing(path)

    def test_combines_726_private_previews_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            original, patch, merged = [base / n for n in ('base.zip', 'patch.zip', 'merged.zip')]
            blob, _ = build_ds3m_v2(*quad())
            baseline = [n for n in range(734) if n not in (721, 722, 723, 724, *MISSING)]
            self.assertEqual(len(baseline), 726)
            with zipfile.ZipFile(original, 'w') as z:
                for n in baseline:
                    z.writestr(f'preview/p{n:03d}.ds3m', blob)
            with zipfile.ZipFile(patch, 'w') as z:
                for n in MISSING:
                    z.writestr(f'preview/p{n:03d}.ds3m', blob)
                z.writestr('C135_PRIVATE_README.txt', 'synthetic')
            result = combine_private_nitrofs(original, patch, merged)
            self.assertEqual(result['preview_models'], 730)
            self.assertFalse(result['release_ready'])
            with zipfile.ZipFile(merged) as z:
                self.assertEqual(len(z.namelist()), 731)
            with zipfile.ZipFile(original, 'a') as z:
                z.writestr('preview/p730.ds3m', blob)
            with self.assertRaisesRegex(ValueError, 'model already present'):
                combine_private_nitrofs(original, patch, merged)

    def test_reject_incomplete_reference_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'bad.zip'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('C56_validation.csv',
                           'model,status,sha256\np730,strict_valid,' + '0'*64 + '\n')
            with self.assertRaisesRegex(ValueError, 'incomplete original C56'):
                read_c56_reference(path)

    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'private NumPy geometry research dependency unavailable')
    def test_unique_c5_source_geometry_recovery(self):
        from c135_c5_geometry import recover
        solutions = recover(synthetic_c5())
        self.assertEqual(len(solutions), 1)
        _, vertices, mesh_groups, areas = solutions[0]
        self.assertEqual(len(vertices), 1)
        self.assertEqual(len(mesh_groups[0][1]), 2)
        self.assertGreater(areas[0], 0)
        blob, report = build_ds3m_v2(vertices, [mesh_groups[0][1]])
        self.assertEqual(report['source_triangles'], 2)
        self.assertEqual(len(blob), 16 + 2*21)


if __name__ == '__main__':
    unittest.main()