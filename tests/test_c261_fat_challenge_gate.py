"""Synthetic fail-closed native challenge persistence checks."""
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from c261_fat_challenge_gate import check


def make_slot(magic, size, crc_at, version, challenge_total=1, correct=0, page=6):
    data = bytearray(size)
    data[:4] = magic
    data[4] = version
    struct.pack_into('<I', data, 8, 1)
    if magic == b'P3SV':
        data[16] = 1
        struct.pack_into('<H', data, 20, 0)
        struct.pack_into('<II', data, 32, correct, challenge_total)
    else:
        data[13] = page
    struct.pack_into('<I', data, crc_at, zlib.crc32(data[:crc_at]))
    return data


class ChallengeFatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a = self.root / 'pokedex3d_A.sav'
        self.r = self.root / 'pokedex3d_resume_A.sav'
        self.a.write_bytes(make_slot(b'P3SV', 64, 60, 1))
        self.r.write_bytes(make_slot(b'P3RV', 80, 76, 3))

    def test_valid_progress(self):
        self.assertEqual(check(self.root)['challenge_answers'], 1)

    def test_zero_answers_rejected(self):
        self.a.write_bytes(make_slot(b'P3SV', 64, 60, 1, challenge_total=0))
        with self.assertRaises(ValueError): check(self.root)

    def test_impossible_score_rejected(self):
        self.a.write_bytes(make_slot(b'P3SV', 64, 60, 1, challenge_total=1, correct=2))
        with self.assertRaises(ValueError): check(self.root)

    def test_wrong_resume_page_rejected(self):
        self.r.write_bytes(make_slot(b'P3RV', 80, 76, 3, page=1))
        with self.assertRaises(ValueError): check(self.root)

    def test_corrupt_progress_crc_rejected(self):
        data = self.a.read_bytes(); self.a.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
        with self.assertRaises(ValueError): check(self.root)

if __name__ == '__main__': unittest.main()
