"""C251: synthetic-only native NitroFS staging acceptance and fail-closed guards."""
from pathlib import Path
import json
import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c251_synthetic_rom_stage import prepare


class C251SyntheticRomStageTests(unittest.TestCase):
    def test_two_diagnostic_native_pairs_and_map_only(self):
        with tempfile.TemporaryDirectory(prefix="c251-") as tmp:
            destination = prepare(Path(tmp))
            self.assertTrue((destination / "models/species_map.p3sm").is_file())
            self.assertEqual(len(list((destination / "geometry").iterdir())), 4)
            report = json.loads((destination / "C249_PRIVATE_DIAGNOSTIC_REPORT.json").read_text())
            self.assertEqual(report["unique_models"], 2)
            self.assertFalse(report["original_game_release_ready"])
            for path in destination.rglob("*"):
                expected = 0o700 if path.is_dir() else 0o600
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected)

    def test_existing_or_nonempty_destination_rejected(self):
        with tempfile.TemporaryDirectory(prefix="c251-") as tmp:
            root = Path(tmp)
            (root / "existing").write_text("keep")
            with self.assertRaisesRegex(ValueError, "empty"):
                prepare(root)
            self.assertEqual((root / "existing").read_text(), "keep")

    def test_symlinked_temp_root_rejected(self):
        with tempfile.TemporaryDirectory(prefix="c251-") as tmp:
            root = Path(tmp)
            link = root.parent / (root.name + "-link")
            try:
                link.symlink_to(root, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    prepare(link)
            finally:
                link.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
