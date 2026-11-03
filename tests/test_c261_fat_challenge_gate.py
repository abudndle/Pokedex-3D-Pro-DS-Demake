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


def active_v4(*, pokemon=500, corrupt_choices=False, total=1, rounds=0):
    data = make_slot(b'P3RV', 144, 140, 4, page=6)
    data[76] = 1
    data[77] = 1           # QUESTION
    data[78] = 0           # first Challenge region
    data[79] = 1           # second question
    data[82] = 0           # answer slot
    struct.pack_into('<H', data, 84, pokemon)
    choices = [pokemon, 501, 502, 503]
    if corrupt_choices:
        choices[1] = pokemon
    struct.pack_into('<4H', data, 86, *choices)
    struct.pack_into('<10H', data, 94, 499, pokemon, *([0]*8))
    struct.pack_into('<I', data, 114, 0x12345678)
    struct.pack_into('<III', data, 118, total, 0, rounds)
    struct.pack_into('<I', data, 140, zlib.crc32(data[:140]))
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

    def test_v4_active_second_question(self):
        self.r.write_bytes(active_v4())
        data = check(self.root, require_active=True)
        self.assertEqual(data['challenge_answers'], 1)
        self.assertTrue(data['active_second_question_v4'])

    def test_legacy_v3_not_mistaken_for_active_v4(self):
        with self.assertRaisesRegex(ValueError, 'active P3RV v4'):
            check(self.root, require_active=True)

    def test_crc_valid_duplicate_option_still_rejected(self):
        self.r.write_bytes(active_v4(corrupt_choices=True))
        with self.assertRaisesRegex(ValueError, 'question identity'):
            check(self.root, require_active=True)

    def test_inconsistent_saved_answer_count_rejected(self):
        self.r.write_bytes(active_v4(total=0))
        with self.assertRaisesRegex(ValueError, 'question identity'):
            check(self.root, require_active=True)

    def test_record_generation_rejects_completed_older_round(self):
        self.r.write_bytes(active_v4(rounds=1))
        with self.assertRaisesRegex(ValueError, 'question identity'):
            check(self.root, require_active=True)

    def test_torn_v4_must_not_fall_back_to_prefix(self):
        self.r.write_bytes(active_v4()[:80])
        with self.assertRaisesRegex(ValueError, 'no valid P3RV'):
            check(self.root, require_active=True)

    def test_v4_crc_corruption_rejected(self):
        data = active_v4()
        data[84] ^= 1
        self.r.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'no valid P3RV'):
            check(self.root, require_active=True)


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
