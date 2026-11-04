from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from test_c262_melonds_challenge_phase_gate import make_frame as xwd
from c358_evolution_gate import verify_fat,verify_frames


class EvolutionGateTests(unittest.TestCase):
    def test_checkpoint_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=bytearray(96);b[:5]=b'P3RV\x05';b[13]=1;b[76]=3
            struct.pack_into('<H',b,16,648);struct.pack_into('<H',b,20,648)
            def save():
                struct.pack_into('<I',b,92,zlib.crc32(b[:92]))
                (root/'pokedex3d_resume_A.sav').write_bytes(b)
            save();verify_fat(root,648)
            for at in (4,12,13,16,20,24,76):
                b[at]^=1;save()
                with self.assertRaises(ValueError):verify_fat(root,648)
                b[at]^=1

    def test_wrong_or_missing_navigation_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/f'{i}.xwd' for i in range(8)]
            # Reuse independently authored patterned XWD fixture generator.
            ids=(0,1,1,1,0,2,2,2)
            for p,n in zip(paths,ids):xwd(p,n)
            self.assertTrue(verify_frames(*paths)['detail_resume'])
            for i in range(8):
                xwd(paths[i],3)
                with self.assertRaises(ValueError):verify_frames(*paths)
                xwd(paths[i],ids[i])


if __name__=='__main__':unittest.main()
