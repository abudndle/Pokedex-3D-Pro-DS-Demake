from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from c355_album_view_gate import synthetic_photo
from c356_photo_resume_gate import verify_fat, verify_frames
from test_c355_album_view_gate import capture


class ResumeGateTests(unittest.TestCase):
    def test_pixels_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/f'{n}.xwd' for n in range(4)]
            for p,n in zip(paths,(8,8,8,None)):capture(p,n)
            self.assertTrue(verify_frames(*paths)['changed_photo_rejected'])
            for i in range(3):
                capture(paths[i],9)
                with self.assertRaises(ValueError):verify_frames(*paths)
                capture(paths[i],8)
            for n in (7,8):
                capture(paths[3],n)
                with self.assertRaises(ValueError):verify_frames(*paths)

    def test_checkpoint_and_roster(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/'Pokedex 3D Pro'/'Photos';folder.mkdir(parents=True)
            for n in range(1,10):(folder/f'AR_{n:04d}.png').write_bytes(synthetic_photo(n))
            b=bytearray(96);b[:5]=b'P3RV\x07';b[13]=8;b[26]=1;b[76]=1;b[78]=8
            original=synthetic_photo(8)
            struct.pack_into('<II',b,80,zlib.crc32(original),len(original))
            def save():
                struct.pack_into('<I',b,92,zlib.crc32(b[:92]))
                (root/'pokedex3d_resume_A.sav').write_bytes(b)
            save();verify_fat(root,'saved')
            for at in (77,78,80,84,88):
                b[at]^=1;save()
                with self.assertRaises(ValueError):verify_fat(root,'saved')
                b[at]^=1
            save();(folder/'AR_0010.png').write_bytes(synthetic_photo(10))
            b[26]=2;save();verify_fat(root,'reordered')
            (folder/'AR_0008.png').write_bytes(synthetic_photo(7))
            with self.assertRaises(ValueError):verify_fat(root,'changed')
            b=bytearray(80);b[:5]=b'P3RV\x03';b[13]=8
            struct.pack_into('<I',b,76,zlib.crc32(b[:76]))
            (root/'pokedex3d_resume_A.sav').write_bytes(b)
            verify_fat(root,'changed')


if __name__=='__main__':unittest.main()
