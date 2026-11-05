from pathlib import Path
import struct,tempfile,unittest,zlib
from test_c262_melonds_challenge_phase_gate import make_frame
from c360_move_gate import verify_fat,verify_frames
class MoveGateTests(unittest.TestCase):
    def test_stale_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=bytearray(80);b[:5]=b'P3RV\x03';b[13]=3;b[18]=1
            def save():
                struct.pack_into('<I',b,76,zlib.crc32(b[:76]));(root/'pokedex3d_resume_A.sav').write_bytes(b)
            save();verify_fat(root)
            for at in (13,18,28,32):
                b[at]^=1;save()
                with self.assertRaises(ValueError):verify_fat(root)
                b[at]^=1
    def test_missing_scroll_and_wrong_touch_or_resume(self):
        with tempfile.TemporaryDirectory() as d:
            ps=[Path(d)/f'{i}.xwd' for i in range(5)];ids=(0,1,2,1,1)
            for p,n in zip(ps,ids):make_frame(p,n)
            verify_frames(*ps)
            for i in (2,3,4):
                make_frame(ps[i],0)
                with self.assertRaises(ValueError):verify_frames(*ps)
                make_frame(ps[i],ids[i])
if __name__=='__main__':unittest.main()
