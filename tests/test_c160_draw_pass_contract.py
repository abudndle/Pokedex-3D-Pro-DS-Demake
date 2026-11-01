"""Synthetic regression coverage; no original game content."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from c160_draw_pass_contract import parse_draws, classify_meshes

def fixture(mode=0x0c02, material=0, index_count=3):
    b = bytearray(240)
    b[:2] = b"\xc5x"
    struct.pack_into("<H", b, 0x10, 1)
    struct.pack_into("<2H", b, 0x14, 1, 1)
    struct.pack_into("<H", b, 0x18, 1)
    struct.pack_into("<3I", b, 0x3c, 120, 140, 152)
    struct.pack_into("<I", b, 0x50, 192)
    struct.pack_into("<I", b, 148, index_count)
    struct.pack_into("<8H", b, 152, material, 0, 0, 0, 1, 0, 0, mode)
    return b

class DrawPassContractTests(unittest.TestCase):
    def test_primary(self):
        meshes, rows = parse_draws(fixture())
        self.assertEqual(classify_meshes(meshes, rows)[0]["primary_material"], 0)
    def test_secondary_only(self):
        meshes, rows = parse_draws(fixture(mode=0x0c01))
        result = classify_meshes(meshes, rows)[0]
        self.assertIsNone(result["primary_material"])
        self.assertEqual(result["secondary_materials"], [0])
    def test_invalid_pass_rejected(self):
        with self.assertRaises(ValueError):
            parse_draws(fixture(mode=0x0c03))
    def test_invalid_material_rejected(self):
        with self.assertRaises(ValueError):
            parse_draws(fixture(material=1))
    def test_invalid_face_count_rejected(self):
        with self.assertRaises(ValueError):
            parse_draws(fixture(index_count=6))

if __name__ == "__main__":
    unittest.main()
