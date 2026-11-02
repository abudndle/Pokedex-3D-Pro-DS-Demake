"""Asset-free deterministic SDL2 DeSmuME CLI keymap tests."""
import configparser
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from c236_desmume_keymap import KEYS, SDL_SCANCODE_MASK, write_config


class TestC236Keymap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_all_upstream_cli_key_names(self):
        self.assertEqual(set(KEYS), {
            "A", "B", "Select", "Start", "Right", "Left", "Up", "Down",
            "R", "L", "X", "Y", "Debug", "Boost", "Lid"})

    def test_distinct_bindings(self):
        self.assertEqual(len(set(KEYS.values())), len(KEYS))

    def test_printable_directional_keycodes(self):
        self.assertEqual([KEYS[k] for k in ("Right", "Left", "Up", "Down")],
                         [ord(c) for c in "dfik"])
        self.assertNotEqual(KEYS["Right"], SDL_SCANCODE_MASK | 79)
        self.assertNotEqual(KEYS["Right"], 275)  # SDL 1.2, not SDL2

    def test_a_b_are_upstream_cli_defaults(self):
        self.assertEqual((KEYS["A"], KEYS["B"]), (120, 98))

    def test_writes_private_glib_keyfile(self):
        path = write_config(self.root)
        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        self.assertEqual(cfg.read(path), [str(path)])
        self.assertEqual({k: int(v) for k, v in cfg["SDLKEYS"].items()}, KEYS)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

    def test_refuses_existing_config_without_modification(self):
        path = write_config(self.root)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            write_config(self.root)
        self.assertEqual(path.read_bytes(), original)

    def test_refuses_symlinked_config_directory(self):
        (self.root / "desmume").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            write_config(self.root)

    def test_refuses_nonexistent_root(self):
        with self.assertRaises(ValueError):
            write_config(self.root / "missing")


if __name__ == "__main__":
    unittest.main()
