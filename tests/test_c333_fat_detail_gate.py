"""C333 synthetic reject/accept gates for real FAT detail-tab checkpoint."""
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from c333_fat_detail_gate import check

def fixture(magic,version,size,offset):
    b=bytearray(size)
    b[:4]=magic;b[4]=version
    struct.pack_into('<I',b,8,1)
    if magic==b'P3SV':b[16]=1
    else:b[13]=1
    if version==5:b[76]=1
    struct.pack_into('<I',b,offset,zlib.crc32(b[:offset]))
    return b

class C333FatTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root=Path(self.dir.name)
        (self.root/'pokedex3d_A.sav').write_bytes(fixture(b'P3SV',1,64,60))
        self.p=self.root/'pokedex3d_resume_A.sav'
        self.p.write_bytes(fixture(b'P3RV',5,96,92))
    def test_valid_detail_checkpoint(self):
        self.assertEqual(check(self.root)['detail_tab'],1)
    def test_legacy_page_only_checkpoint_rejected(self):
        self.p.write_bytes(fixture(b'P3RV',3,80,76))
        with self.assertRaisesRegex(ValueError,'detail tab v5'):
            check(self.root)
    def test_crc_valid_hidden_reserved_bytes_rejected(self):
        b=bytearray(self.p.read_bytes());b[78]=1
        struct.pack_into('<I',b,92,zlib.crc32(b[:92]))
        self.p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'no valid P3RV'):check(self.root)
    def test_wrong_detail_tab_rejected(self):
        b=bytearray(self.p.read_bytes());b[76]=2
        struct.pack_into('<I',b,92,zlib.crc32(b[:92]))
        self.p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'detail tab v5'):check(self.root)
    def test_torn_data_rejected(self):
        self.p.write_bytes(self.p.read_bytes()[:80])
        with self.assertRaisesRegex(ValueError,'no valid P3RV'):check(self.root)
    def test_corrupt_crc_rejected(self):
        b=bytearray(self.p.read_bytes());b[16]^=1;self.p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'no valid P3RV'):check(self.root)
    def test_wrong_species_rejected(self):
        b=bytearray(self.p.read_bytes());b[16]=25
        struct.pack_into('<I',b,92,zlib.crc32(b[:92]))
        self.p.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'incorrect species'):check(self.root)
    def test_favorite_lost_rejected(self):
        b=bytearray((self.root/'pokedex3d_A.sav').read_bytes());b[16]=0
        struct.pack_into('<I',b,60,zlib.crc32(b[:60]))
        (self.root/'pokedex3d_A.sav').write_bytes(b)
        with self.assertRaisesRegex(ValueError,'favorite missing'):check(self.root)
if __name__=='__main__':unittest.main()
