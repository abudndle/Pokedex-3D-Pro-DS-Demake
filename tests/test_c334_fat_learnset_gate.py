import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from c334_fat_learnset_gate import check
from c334_synthetic_learnset import payload


class LearnsetFatTests(unittest.TestCase):
    def fixture(self):
        b = bytearray(96)
        b[:5] = b'P3RV\x06'
        b[8] = 1
        b[13] = 1
        b[76:78] = bytes((4, 1))
        b[80:84] = payload()[12:16]
        return b

    def run_gate(self, b):
        struct.pack_into('<I', b, 92, zlib.crc32(b[:92]))
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'pokedex3d_resume_A.sav').write_bytes(b)
            return check(d)

    def test_exact_page(self):
        self.assertEqual(self.run_gate(self.fixture())['page'], 1)

    def test_reject_wrong_identity_page_or_source(self):
        for offset, value in [(4, 7), (12, 1), (13, 2), (16, 1), (24, 1),
                              (76, 3), (77, 0), (77, 64), (78, 1), (79, 1),
                              (80, 0), (84, 1), (91, 1)]:
            with self.subTest(offset=offset, value=value):
                b = self.fixture()
                b[offset] = value
                with self.assertRaises(ValueError):
                    self.run_gate(b)

    def test_reject_crc_corruption(self):
        b = self.fixture()
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'pokedex3d_resume_A.sav').write_bytes(b)
            with self.assertRaises(ValueError):
                check(d)


if __name__ == '__main__':
    unittest.main()
