"""Synthetic fail-closed P3RC visit/recent/round FAT checks."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c263_fat_records_gate import check


def make_records(*, viewed=1, recent=0, rounds=0, runs=0, version=1):
    b = bytearray(160)
    b[:4] = b'P3RC'
    b[4] = version
    struct.pack_into('<I', b, 8, 1)
    b[16] = viewed
    struct.pack_into('<H', b, 100, recent)
    for i in range(1, 8):
        struct.pack_into('<H', b, 100 + i * 2, 0xFFFF)
    struct.pack_into('<H', b, 116, runs)
    b[130:137] = bytes([0xFF]) * 7
    struct.pack_into('<I', b, 140, rounds)
    struct.pack_into('<I', b, 156, zlib.crc32(b[:156]))
    return b


class C263RecordsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.slot = self.root / 'pokedex3d_records_A.sav'
        self.slot.write_bytes(make_records())

    def test_valid_single_visit(self):
        self.assertTrue(check(self.root)['recent_001'])

    def test_missing_viewed_species_rejected(self):
        self.slot.write_bytes(make_records(viewed=0))
        with self.assertRaisesRegex(ValueError, 'viewed'):
            check(self.root)

    def test_phantom_species_rejected(self):
        self.slot.write_bytes(make_records(viewed=3))
        with self.assertRaisesRegex(ValueError, 'viewed'):
            check(self.root)

    def test_wrong_recent_species_rejected(self):
        self.slot.write_bytes(make_records(recent=1))
        with self.assertRaisesRegex(ValueError, 'recent'):
            check(self.root)

    def test_incomplete_challenge_round_rejected(self):
        self.slot.write_bytes(make_records(rounds=1))
        with self.assertRaisesRegex(ValueError, 'round'):
            check(self.root)

    def test_bad_crc_rejected(self):
        b = make_records(); b[16] ^= 1; self.slot.write_bytes(b)
        with self.assertRaises(ValueError):
            check(self.root)

    def test_missing_slot_rejected(self):
        self.slot.unlink()
        with self.assertRaises(ValueError):
            check(self.root)

    def test_wrong_version_rejected(self):
        self.slot.write_bytes(make_records(version=2))
        with self.assertRaisesRegex(ValueError, 'version'):
            check(self.root)


if __name__ == '__main__':
    unittest.main()
