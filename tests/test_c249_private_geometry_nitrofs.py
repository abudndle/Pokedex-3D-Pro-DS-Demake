"""C249 synthetic-only diagnostic species-to-private-native-geometry staging tests."""
from pathlib import Path
import json
import os
import stat
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c249_private_geometry_nitrofs import stage, parse_assignments


def synthetic_pair(model):
    table = struct.pack('<HHI', 0, 3, 0)
    xyz = struct.pack('<9h', 0, 0, 0, 4096, 0, 0, 0, 4096, 0)
    vx = struct.pack('<4sHHHHI', b'P3VX', 1, model, 1, 0,
                     zlib.crc32(table + xyz)) + table + xyz
    ix = struct.pack('<4sHHH', b'P3IX', 1, model, 1) + struct.pack('<HI3H', 0, 1, 0, 1, 2)
    return vx, ix


def fixture(root, assignments=None):
    source = root / 'source'
    source.mkdir()
    for model in (2, 3):
        vx, ix = synthetic_pair(model)
        (source / f'p{model:03d}.p3vx').write_bytes(vx)
        (source / f'p{model:03d}.p3ix').write_bytes(ix)
    mapping = root / 'mapping.json'
    mapping.write_text(json.dumps({'purpose': 'diagnostic', 'assignments': assignments or [
        {'species': 1, 'model': 2}, {'species': 649, 'model': 3}]}))
    return source, mapping, root / 'staged'


class C249PrivateGeometryNitroFsTests(unittest.TestCase):
    def test_diagnostic_pair_and_species_map_staged_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            report = stage(source, mapping, dest)
            self.assertEqual((report['species_slots'], report['unique_models']), (2, 2))
            self.assertFalse(report['original_species_resource_mapping_verified'])
            self.assertFalse(report['asset_integrated_emulator_verified'])
            p3sm = (dest / 'models/species_map.p3sm').read_bytes()
            self.assertEqual(len(p3sm), 1306)
            self.assertEqual(struct.unpack_from('<4sHH', p3sm), (b'P3SM', 1, 649))
            self.assertEqual(struct.unpack_from('<H', p3sm, 8)[0], 2)
            self.assertEqual(struct.unpack_from('<H', p3sm, 10)[0], 0xffff)
            self.assertEqual(struct.unpack_from('<H', p3sm, 8 + 648 * 2)[0], 3)
            self.assertEqual({p.name for p in (dest / 'geometry').iterdir()},
                             {'p002.p3vx', 'p002.p3ix', 'p003.p3vx', 'p003.p3ix'})
            for path in dest.rglob('*'):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)
            self.assertFalse(json.loads((dest / 'C249_PRIVATE_DIAGNOSTIC_REPORT.json').read_text())
                             ['original_game_release_ready'])

    def test_reject_duplicate_species_slot(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            parse_assignments(json.dumps({'purpose': 'diagnostic', 'assignments': [
                {'species': 1, 'model': 2}, {'species': 1, 'model': 3}]}).encode())

    def test_allow_multiple_species_slots_one_model_without_duplicate_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp), [
                {'species': 1, 'model': 2}, {'species': 2, 'model': 2}])
            report = stage(source, mapping, dest)
            self.assertEqual((report['species_slots'], report['unique_models']), (2, 1))
            self.assertEqual(len(list((dest / 'geometry').iterdir())), 2)

    def test_never_infer_original_mapping(self):
        for purpose in ('original', 'source_verified', 'release', ''):
            with self.subTest(purpose=purpose), self.assertRaisesRegex(ValueError, 'diagnostic'):
                parse_assignments(json.dumps({'purpose': purpose, 'assignments': [
                    {'species': 1, 'model': 2}]}).encode())

    def test_reject_out_of_range_reserved_and_boolean_ids(self):
        for species, model in ((0, 2), (650, 2), (1, 721), (1, 738), (True, 2), (1, True)):
            with self.subTest(species=species, model=model), self.assertRaises(ValueError):
                parse_assignments(json.dumps({'purpose': 'diagnostic', 'assignments': [
                    {'species': species, 'model': model}]}).encode())

    def test_corrupt_native_pair_rejected_without_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            path = source / 'p003.p3vx'
            data = bytearray(path.read_bytes())
            data[-1] ^= 1
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                stage(source, mapping, dest)
            self.assertFalse(dest.exists())
            self.assertEqual(list(Path(tmp).glob('.c249-*')), [])

    def test_missing_index_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            (source / 'p002.p3ix').unlink()
            with self.assertRaises(OSError):
                stage(source, mapping, dest)
            self.assertFalse(dest.exists())

    def test_hardlinked_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            os.link(source / 'p002.p3vx', Path(tmp) / 'alias')
            with self.assertRaisesRegex(ValueError, 'single-link'):
                stage(source, mapping, dest)
            self.assertFalse(dest.exists())

    def test_symlinked_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            original = source / 'p002.p3ix'
            original.rename(source / 'hidden')
            original.symlink_to(source / 'hidden')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                stage(source, mapping, dest)
            self.assertFalse(dest.exists())

    def test_existing_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            dest.mkdir()
            marker = dest / 'keep'
            marker.write_text('do not replace')
            with self.assertRaisesRegex(ValueError, 'must not exist'):
                stage(source, mapping, dest)
            self.assertEqual(marker.read_text(), 'do not replace')

    def test_source_identity_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, mapping, dest = fixture(Path(tmp))
            path = source / 'p003.p3ix'
            data = bytearray(path.read_bytes())
            struct.pack_into('<H', data, 6, 2)
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                stage(source, mapping, dest)
            self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()
