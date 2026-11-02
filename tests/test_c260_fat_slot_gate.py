"""Asset-free synthetic FAT slot checks; no emulator or Nintendo bytes."""
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from c260_fat_slot_gate import check


def slot(magic, size, crc_offset, version, seq):
    data = bytearray(size)
    data[:4] = magic
    data[4] = version
    struct.pack_into('<I', data, 8, seq)
    if magic == b'P3SV':
        data[16] = 1
        struct.pack_into('<H', data, 20, 0)
    else:
        data[12] = 0
        data[13] = 1
    struct.pack_into('<I', data, crc_offset, zlib.crc32(data[:crc_offset]))
    return bytes(data)


class FatSlotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'pokedex3d_A.sav').write_bytes(slot(b'P3SV', 64, 60, 1, 1))
        (self.root / 'pokedex3d_resume_A.sav').write_bytes(slot(b'P3RV', 80, 76, 3, 1))

    def test_valid_export(self):
        self.assertTrue(check(self.root)['favorite_000'])

    def test_corrupt_crc_fails_closed(self):
        p = self.root / 'pokedex3d_A.sav'
        data = bytearray(p.read_bytes()); data[20] ^= 1; p.write_bytes(data)
        with self.assertRaises(ValueError): check(self.root)

    def test_truncated_resume_fails_closed(self):
        (self.root / 'pokedex3d_resume_A.sav').write_bytes(b'P3RV')
        with self.assertRaises(ValueError): check(self.root)

    def test_duplicate_casefold_slot_fails_closed(self):
        (self.root / 'POKEDEX3D_A.SAV').write_bytes((self.root / 'pokedex3d_A.sav').read_bytes())
        with self.assertRaises(ValueError): check(self.root)

    def test_newest_valid_slot_selected(self):
        (self.root / 'pokedex3d_B.sav').write_bytes(slot(b'P3SV', 64, 60, 1, 2))
        (self.root / 'pokedex3d_resume_B.sav').write_bytes(slot(b'P3RV', 80, 76, 3, 2))
        self.assertTrue(check(self.root)['resume_dex_000'])

if __name__ == '__main__': unittest.main()
