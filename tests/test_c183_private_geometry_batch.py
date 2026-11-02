"""Asset-free synthetic checks of the private 730-model native batch runner."""
import importlib.util
import pathlib
import stat
import struct
import zlib
import tempfile
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("c183", ROOT / "tools/c183_private_geometry_batch.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PrivateGeometryBatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name) / "pairs"
        self.root.mkdir()
        self.probe = pathlib.Path(self.temp.name) / "probe"
        self.probe.write_text("#!/bin/sh\nexit 0\n")
        self.probe.chmod(self.probe.stat().st_mode | stat.S_IXUSR)

    def pair(self, model, corrupt=False):
        name = f"p{model:03d}"
        payload = struct.pack("<HHI", 7, 3, 0) + b"\\0" * 18
        vx = b"P3VX" + struct.pack("<HHHHI", 1, model, 1, 0, zlib.crc32(payload)) + payload
        (self.root / f"{name}.p3vx").write_bytes(vx)
        data = struct.pack("<4sHHHHI3H", b"P3IX", 1, model, 1, 7, 1, 0, 1, 2)
        (self.root / f"{name}.p3ix").write_bytes(data[:-1] if corrupt else data)

    def test_one_pair_passes_native_probe_without_provenance_claim(self):
        self.pair(14)
        report = mod.audit(self.root, self.probe, {14})
        self.assertTrue(report["all_pairs_verified"])
        self.assertEqual(report["models"]["p014"]["triangles"], 1)
        self.assertFalse(report["original_c5_provenance_verified"])
        self.assertFalse(report["private_asset_emulator_verified"])

    def test_missing_or_corrupt_pair_is_not_verified(self):
        self.pair(14, corrupt=True)
        report = mod.audit(self.root, self.probe, {14, 15})
        self.assertEqual(report["native_pairs_verified"], 0)
        self.assertEqual(report["models"]["p015"]["error"], "missing_pair")
        self.assertIn("error", report["models"]["p014"])

    def test_native_probe_failure_is_not_success(self):
        self.pair(14)
        self.probe.write_text("#!/bin/sh\nexit 1\n")
        report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report["all_pairs_verified"])

    def test_native_probe_receives_correct_pair_model_and_triangle_count(self):
        self.pair(14)
        with unittest.mock.patch.object(mod.subprocess, 'run', return_value=unittest.mock.Mock(returncode=0)) as run:
            report = mod.audit(self.root, self.probe, {14})
        self.assertTrue(report['all_pairs_verified'])
        args = run.call_args.args[0]
        self.assertEqual(args, [str(self.probe), str(self.root / 'p014.p3vx'),
                                str(self.root / 'p014.p3ix'), '14', '1'])
        self.assertEqual(run.call_args.kwargs['timeout'], 15)

    def test_native_probe_runs_without_shell_and_discards_output(self):
        self.pair(14)
        with unittest.mock.patch.object(mod.subprocess, 'run', return_value=unittest.mock.Mock(returncode=0)) as run:
            report = mod.audit(self.root, self.probe, {14})
        self.assertTrue(report['all_pairs_verified'])
        self.assertIsInstance(run.call_args.args[0], list)
        self.assertFalse(run.call_args.kwargs.get('shell', False))
        self.assertIs(run.call_args.kwargs['stdout'], mod.subprocess.DEVNULL)
        self.assertIs(run.call_args.kwargs['stderr'], mod.subprocess.DEVNULL)
        self.assertFalse(run.call_args.kwargs['check'])

    def test_partial_native_probe_failure_preserves_successful_pair(self):
        self.pair(14)
        self.pair(15)
        outcomes = [unittest.mock.Mock(returncode=0), unittest.mock.Mock(returncode=3)]
        with unittest.mock.patch.object(mod.subprocess, 'run', side_effect=outcomes) as run:
            report = mod.audit(self.root, self.probe, {15, 14})
        self.assertEqual(run.call_count, 2)
        self.assertEqual(report['expected'], 2)
        self.assertEqual(report['native_pairs_verified'], 1)
        self.assertFalse(report['all_pairs_verified'])
        self.assertTrue(report['models']['p014']['native_gl_path_verified'])
        self.assertEqual(report['models']['p015']['error'], 'ValueError')
        self.assertFalse(report['original_c5_provenance_verified'])
        self.assertFalse(report['private_asset_emulator_verified'])

    def test_reject_degenerate_triangle_before_native_probe(self):
        for vertices in ((1, 1, 2), (1, 2, 2), (1, 2, 1)):
            with self.subTest(vertices=vertices):
                self.pair(14)
                (self.root / 'p014.p3ix').write_bytes(
                    struct.pack('<4sHHHHI3H', b'P3IX', 1, 14, 1, 7, 1, *vertices))
                with unittest.mock.patch.object(mod.subprocess, 'run') as run:
                    report = mod.audit(self.root, self.probe, {14})
                self.assertEqual(report['models']['p014']['error'], 'ValueError')
                self.assertEqual(report['native_pairs_verified'], 0)
                run.assert_not_called()

    def test_index_vertex_capacity_boundary(self):
        self.pair(14)
        index = self.root / 'p014.p3ix'
        index.write_bytes(struct.pack('<4sHHHHI3H', b'P3IX', 1, 14, 1, 7, 1, 0, 1, 8192))
        with unittest.mock.patch.object(mod.subprocess, 'run') as run:
            report = mod.audit(self.root, self.probe, {14})
        self.assertEqual(report['models']['p014']['error'], 'ValueError')
        self.assertEqual(report['native_pairs_verified'], 0)
        run.assert_not_called()
        index.write_bytes(struct.pack('<4sHHHHI3H', b'P3IX', 1, 14, 1, 7, 1, 0, 1, 8191))
        with unittest.mock.patch.object(mod.subprocess, 'run', return_value=unittest.mock.Mock(returncode=0)) as run:
            report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report['all_pairs_verified'])
        run.assert_not_called()

    def test_reject_index_triangle_count_above_global_limit(self):
        self.pair(14)
        index = self.root / 'p014.p3ix'
        index.write_bytes(struct.pack('<4sHHHHI', b'P3IX', 1, 14, 1, 7, 1801))
        with unittest.mock.patch.object(mod.subprocess, 'run') as run:
            report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report['all_pairs_verified'])
        self.assertEqual(report['native_pairs_verified'], 0)
        self.assertEqual(report['models']['p014']['error'], 'ValueError')
        run.assert_not_called()

    def test_multiple_valid_pairs_are_all_counted(self):
        self.pair(14)
        self.pair(15)
        with unittest.mock.patch.object(mod.subprocess, 'run', return_value=unittest.mock.Mock(returncode=0)) as run:
            report = mod.audit(self.root, self.probe, {15, 14})
        self.assertEqual(report['expected'], 2)
        self.assertEqual(report['native_pairs_verified'], 2)
        self.assertTrue(report['all_pairs_verified'])
        self.assertEqual(set(report['models']), {'p014', 'p015'})
        self.assertTrue(all(record['native_gl_path_verified'] for record in report['models'].values()))
        self.assertEqual(run.call_count, 2)
        self.assertEqual([call.args[0][3] for call in run.call_args_list], ['14', '15'])
        self.assertFalse(report['original_c5_provenance_verified'])
        self.assertFalse(report['private_asset_emulator_verified'])

    def test_mixed_pair_outcomes_count_only_verified_models(self):
        self.pair(14)
        self.pair(15, corrupt=True)
        report = mod.audit(self.root, self.probe, {14, 15, 16})
        self.assertEqual(report['expected'], 3)
        self.assertEqual(report['native_pairs_verified'], 1)
        self.assertFalse(report['all_pairs_verified'])
        self.assertTrue(report['models']['p014']['native_gl_path_verified'])
        self.assertEqual(report['models']['p015']['error'], 'ValueError')
        self.assertEqual(report['models']['p016']['error'], 'missing_pair')
        self.assertFalse(report['original_c5_provenance_verified'])
        self.assertFalse(report['private_asset_emulator_verified'])

    def test_native_probe_nonzero_exit_records_failure(self):
        self.pair(14)
        with unittest.mock.patch.object(mod.subprocess, 'run', return_value=unittest.mock.Mock(returncode=127)) as run:
            report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report['all_pairs_verified'])
        self.assertEqual(report['native_pairs_verified'], 0)
        self.assertEqual(report['models']['p014']['error'], 'ValueError')
        self.assertEqual(run.call_args.kwargs['timeout'], 15)
        self.assertFalse(run.call_args.kwargs['check'])

    def test_native_probe_launch_oserror_is_not_success(self):
        self.pair(14)
        with unittest.mock.patch.object(mod.subprocess, 'run', side_effect=OSError('synthetic launch failure')):
            report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report['all_pairs_verified'])
        self.assertEqual(report['native_pairs_verified'], 0)
        self.assertEqual(report['models']['p014']['error'], 'OSError')

    def test_native_probe_timeout_is_not_success(self):
        self.pair(14)
        with unittest.mock.patch.object(mod.subprocess, 'run', side_effect=mod.subprocess.TimeoutExpired(cmd=['probe'], timeout=15)):
            report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report['all_pairs_verified'])
        self.assertEqual(report['native_pairs_verified'], 0)
        self.assertEqual(report['models']['p014']['error'], 'TimeoutExpired')

    def test_reject_extra_or_out_of_roster_files(self):
        self.pair(14)
        (self.root / "p721.p3ix").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            mod.audit(self.root, self.probe, {14})

    def test_reject_symlink_without_following(self):
        self.pair(14)
        index = self.root / "p014.p3ix"
        target = pathlib.Path(self.temp.name) / "outside"
        target.write_bytes(index.read_bytes())
        index.unlink()
        index.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "unexpected"):
            mod.audit(self.root, self.probe, {14})

    def test_duplicate_roster_is_invalid(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            mod.audit(self.root, self.probe, [14, 14])

    def test_boolean_roster_is_invalid(self):
        with self.assertRaisesRegex(ValueError, 'invalid model roster'):
            mod.audit(self.root, self.probe, [True])

    def test_reject_index_mesh_identifier_out_of_range(self):
        self.pair(14)
        (self.root / 'p014.p3ix').write_bytes(
            struct.pack('<4sHHHHI3H', b'P3IX', 1, 14, 1, 64, 1, 0, 1, 2))
        report = mod.audit(self.root, self.probe, {14})
        self.assertEqual(report['native_pairs_verified'], 0)
        self.assertEqual(report['models']['p014']['error'], 'ValueError')

    def test_empty_roster_is_invalid(self):
        with self.assertRaises(ValueError):
            mod.audit(self.root, self.probe, set())

    def test_reject_probe_symlink(self):
        alias = self.root.parent / 'alias-probe'
        alias.symlink_to(self.probe)
        with self.assertRaisesRegex(ValueError, 'probe symlink'):
            mod.audit(self.root, alias, {14})

    def test_reject_probe_symlinked_parent(self):
        self.pair(14)
        alias = pathlib.Path(self.temp.name) / 'alias-bin'
        alias.symlink_to(self.probe.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'probe symlink'):
            mod.audit(self.root, alias / 'probe', {14})

    def test_reject_probe_broken_symlink(self):
        self.pair(14)
        alias = pathlib.Path(self.temp.name) / 'broken-probe'
        alias.symlink_to(self.root / 'missing-executable')
        with self.assertRaisesRegex(ValueError, 'probe symlink'):
            mod.audit(self.root, alias, {14})

    def test_reject_symlinked_probe_parent(self):
        alias = pathlib.Path(self.temp.name) / 'probe-parent-alias'
        alias.symlink_to(pathlib.Path(self.temp.name), target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'probe symlink'):
            mod.audit(self.root, alias / 'probe', {14})

    def test_probe_must_be_executable(self):
        self.pair(14)
        self.probe.chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'not executable'):
            mod.audit(self.root, self.probe, {14})

    def test_reject_empty_native_probe(self):
        self.pair(14)
        self.probe.write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'probe empty'):
            mod.audit(self.root, self.probe, {14})

    def test_probe_must_be_readable(self):
        self.pair(14)
        self.probe.chmod(0o100)
        with unittest.mock.patch.object(mod.os, 'access', side_effect=lambda path, mode: mode != mod.os.R_OK):
            with self.assertRaisesRegex(ValueError, 'not readable'):
                mod.audit(self.root, self.probe, {14})

    def test_reject_symlinked_root(self):
        alias = pathlib.Path(self.temp.name) / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            mod.audit(alias, self.probe, {14})

    def test_reject_symlinked_parent(self):
        alias = pathlib.Path(self.temp.name) / 'alias'
        alias.symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            mod.audit(alias / 'pairs', self.probe, {14})

    def test_reject_directory_disguised_as_pair(self):
        (self.root / 'p014.p3vx').mkdir()
        with self.assertRaisesRegex(ValueError, 'unexpected'):
            mod.audit(self.root, self.probe, {14})

    def test_private_path_guard(self):
        with self.assertRaisesRegex(ValueError, "outside public repository"):
            mod.outside_repo(ROOT / "nitrofs")

    def test_reject_trailing_bytes(self):
        self.pair(14)
        with (self.root / "p014.p3ix").open("ab") as out:
            out.write(b"X")
        report = mod.audit(self.root, self.probe, {14})
        self.assertFalse(report["all_pairs_verified"])


if __name__ == "__main__":
    unittest.main()
