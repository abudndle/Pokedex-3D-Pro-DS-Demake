"""Synthetic full-round native FAT cross-file consistency tests."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c264_fat_completed_round_gate import check


def slot(magic, size, crc_at, version, *, correct=5, total=10, rounds=1, runs=1, best=5):
    b = bytearray(size); b[:4] = magic; b[4] = version
    struct.pack_into('<I', b, 8, 1)
    if magic == b'P3SV':
        b[16] = 1; struct.pack_into('<H', b, 20, 0)
        struct.pack_into('<II', b, 32, correct, total)
    elif magic == b'P3RV':
        b[13] = 6
    else:
        b[16] = 1
        struct.pack_into('<H', b, 100, 0)
        for i in range(1, 8): struct.pack_into('<H', b, 100+i*2, 0xFFFF)
        struct.pack_into('<H', b, 116, runs)
        b[130:137] = bytes([best]) + bytes([0xFF])*6
        struct.pack_into('<I', b, 140, rounds)
    struct.pack_into('<I', b, crc_at, zlib.crc32(b[:crc_at]))
    return b


class C264Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.s = self.root/'pokedex3d_A.sav'
        self.v = self.root/'pokedex3d_resume_A.sav'
        self.r = self.root/'pokedex3d_records_A.sav'
        self.s.write_bytes(slot(b'P3SV', 64, 60, 1))
        self.v.write_bytes(slot(b'P3RV', 80, 76, 3))
        self.r.write_bytes(slot(b'P3RC', 160, 156, 1))

    def test_valid_completed_round(self):
        self.assertEqual(check(self.root)['rounds'], 1)

    def test_nine_answers_not_complete(self):
        self.s.write_bytes(slot(b'P3SV', 64, 60, 1, total=9))
        with self.assertRaisesRegex(ValueError, 'ten-answer'): check(self.root)

    def test_score_over_total_rejected(self):
        self.s.write_bytes(slot(b'P3SV', 64, 60, 1, correct=11))
        with self.assertRaisesRegex(ValueError, 'ten-answer'): check(self.root)

    def test_missing_round_rejected(self):
        self.r.write_bytes(slot(b'P3RC', 160, 156, 1, rounds=0))
        with self.assertRaisesRegex(ValueError, 'round'): check(self.root)

    def test_missing_run_rejected(self):
        self.r.write_bytes(slot(b'P3RC', 160, 156, 1, runs=0))
        with self.assertRaisesRegex(ValueError, 'round'): check(self.root)

    def test_high_score_mismatch_rejected(self):
        self.r.write_bytes(slot(b'P3RC', 160, 156, 1, best=4))
        with self.assertRaisesRegex(ValueError, 'high score'): check(self.root)

    def test_corrupt_records_crc_rejected(self):
        b = bytearray(self.r.read_bytes()); b[140] ^= 1; self.r.write_bytes(b)
        with self.assertRaises(ValueError): check(self.root)

    def test_missing_resume_rejected(self):
        self.v.unlink()
        with self.assertRaises(ValueError): check(self.root)


if __name__ == '__main__': unittest.main()
