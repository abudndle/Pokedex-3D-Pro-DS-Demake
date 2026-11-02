"""C272 synthetic-only isolated private ROM staging; no Nintendo assets."""
from pathlib import Path
import hashlib
import json
import stat
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c272_private_rom_build import prepare


def fixture(root):
    stage = root / 'stage'
    (stage / 'geometry').mkdir(parents=True)
    (stage / 'models').mkdir()
    model = 200
    table = struct.pack('<HHI', 0, 3, 0)
    xyz = struct.pack('<9h', 0, 0, 0, 4096, 0, 0, 0, 4096, 0)
    vx = struct.pack('<4sHHHHI', b'P3VX', 1, model, 1, 0, zlib.crc32(table + xyz)) + table + xyz
    ix = struct.pack('<4sHHH', b'P3IX', 1, model, 1) + struct.pack('<HI3H', 0, 1, 0, 1, 2)
    (stage / 'geometry/p200.p3vx').write_bytes(vx)
    (stage / 'geometry/p200.p3ix').write_bytes(ix)
    ids = [0xffff] * 649
    ids[0] = model
    (stage / 'models/species_map.p3sm').write_bytes(struct.pack('<4sHH649H', b'P3SM', 1, 649, *ids))
    report = {'schema': 'p3d-c249-private-diagnostic-nitrofs-v1',
              'diagnostic_species_assignments_only': True,
              'original_species_resource_mapping_verified': False,
              'asset_integrated_emulator_verified': False,
              'original_game_release_ready': False,
              'species_slots': 1, 'unique_models': 1,
              'models': {'p200': {'vertices': 3, 'triangles': 1,
                       'native_gl_probe_passed': True,
                       'p3vx_sha256': hashlib.sha256(vx).hexdigest(),
                       'p3ix_sha256': hashlib.sha256(ix).hexdigest()}}}
    (stage / 'C249_PRIVATE_DIAGNOSTIC_REPORT.json').write_text(json.dumps(report))
    return stage


class C272PrivateRomBuildTests(unittest.TestCase):
    def test_clean_nitrofs_excludes_sha_report_and_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = fixture(root)
            nitro = prepare(stage, root / 'result')
            self.assertEqual({p.relative_to(nitro).as_posix() for p in nitro.rglob('*') if p.is_file()},
                             {'models/species_map.p3sm', 'geometry/p200.p3vx', 'geometry/p200.p3ix'})
            self.assertFalse((nitro / 'C249_PRIVATE_DIAGNOSTIC_REPORT.json').exists())
            for p in nitro.rglob('*'):
                self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o700 if p.is_dir() else 0o600)
            self.assertEqual(stat.S_IMODE(nitro.stat().st_mode), 0o700)

    def test_corrupt_geometry_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); stage = fixture(root)
            path = stage / 'geometry/p200.p3vx'
            data = bytearray(path.read_bytes()); data[-1] ^= 1; path.write_bytes(data)
            with self.assertRaises(ValueError):
                prepare(stage, root / 'result')
            self.assertFalse((root / 'result').exists())

    def test_reject_report_hash_and_forged_original_claim(self):
        for mutation in ('hash', 'claim', 'probe'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); stage = fixture(root)
                path = stage / 'C249_PRIVATE_DIAGNOSTIC_REPORT.json'
                data = json.loads(path.read_text())
                if mutation == 'hash': data['models']['p200']['p3ix_sha256'] = '0' * 64
                if mutation == 'claim': data['original_game_release_ready'] = True
                if mutation == 'probe': data['models']['p200']['native_gl_probe_passed'] = False
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    prepare(stage, root / 'result')

    def test_reject_misbound_or_missing_species(self):
        for mutation in ('unmapped', 'wrong-model'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); stage = fixture(root)
                path = stage / 'models/species_map.p3sm'
                data = bytearray(path.read_bytes())
                struct.pack_into('<H', data, 8, 0xffff if mutation == 'unmapped' else 201)
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    prepare(stage, root / 'result')

    def test_reject_extra_file_or_symlink(self):
        for mutation in ('extra', 'symlink'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); stage = fixture(root)
                if mutation == 'extra':
                    (stage / 'geometry/private.sha256').write_text('secret')
                else:
                    (stage / 'geometry/p200.p3ix').unlink()
                    (stage / 'geometry/p200.p3ix').symlink_to(stage / 'geometry/p200.p3vx')
                with self.assertRaises(ValueError):
                    prepare(stage, root / 'result')

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); stage = fixture(root)
            output = root / 'result'; output.mkdir(); (output / 'marker').write_text('keep')
            with self.assertRaises(ValueError):
                prepare(stage, output)
            self.assertEqual((output / 'marker').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
