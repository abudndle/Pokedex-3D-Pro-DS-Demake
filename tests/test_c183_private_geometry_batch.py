"""Asset-free synthetic checks of the private 730-model native batch runner."""
import importlib.util
import pathlib
import stat
import struct
import tempfile
import unittest

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
        (self.root / f"{name}.p3vx").write_bytes(b"synthetic vertex stream")
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

    def test_probe_must_be_executable(self):
        self.pair(14)
        self.probe.chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'not executable'):
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
