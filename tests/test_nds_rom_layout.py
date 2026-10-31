"""Regression tests for NDS executable section bounds."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("rom_check", Path(__file__).resolve().parents[1] / "tools" / "verify_nds_rom.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class RomLayoutTests(unittest.TestCase):
    def check(self, arm9=(0x200, 0x02000000, 0x02000000, 0x40),
              arm7=(0x240, 0x03800000, 0x03800000, 0x40)):
        rom = bytearray(0x300)
        struct.pack_into("<4I", rom, 0x20, *arm9)
        struct.pack_into("<4I", rom, 0x30, *arm7)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test.nds"
            path.write_bytes(rom)
            return module.verify(path)

    def test_disjoint_sections(self):
        self.assertEqual([], self.check())

    def test_overlapping_sections_rejected(self):
        errors = self.check(arm7=(0x220, 0x03800000, 0x03800000, 0x40))
        self.assertTrue(any("overlap" in e for e in errors))

    def test_entry_outside_section_rejected(self):
        errors = self.check(arm9=(0x200, 0x02000100, 0x02000000, 0x40))
        self.assertTrue(any("entry point" in e for e in errors))

    def test_truncated_section_rejected(self):
        errors = self.check(arm9=(0x2F0, 0x02000000, 0x02000000, 0x40))
        self.assertTrue(any("outside ROM" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
