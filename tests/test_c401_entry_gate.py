from pathlib import Path
import struct,tempfile,unittest,zlib
from test_c262_melonds_challenge_phase_gate import make_frame
from c401_entry_gate import verify_fat,verify_frames
class EntryGateTests(unittest.TestCase):
    def test_fat_rejects_mutation_and_stale_context(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);s=bytearray(64);s[:5]=b'P3SV\x01';s[16]=1
            r=bytearray(80);r[:5]=b'P3RV\x03';r[13]=1
            def save():
                for name,b in [('pokedex3d',s),('pokedex3d_resume',r)]:
                    struct.pack_into('<I',b,len(b)-4,zlib.crc32(b[:-4]));(root/(name+'_A.sav')).write_bytes(b)
            save();verify_fat(root,'favorite')
            for data,at in ((s,16),(s,20),(s,12),(r,13),(r,16),(r,20),(r,24),(r,4)):
                data[at]^=1;save()
                with self.assertRaises(ValueError):verify_fat(root,'favorite')
                data[at]^=1
            s[12]=r[16]=r[20]=1;r[13]=3
            save();verify_fat(root,'move')
            for at in (18,28,32):
                r[at]^=1;save()
                with self.assertRaises(ValueError):verify_fat(root,'move')
                r[at]^=1
            save()
            with self.assertRaises(ValueError):verify_fat(root,'scroll')
            r[32]=28;save();verify_fat(root,'scroll')
            r[32]=0;r[28]=1;save();verify_fat(root,'effect')
    def test_frames_reject_missing_flow_and_restart(self):
        with tempfile.TemporaryDirectory() as d:
            ps=[Path(d)/f'{n}.xwd' for n in range(11)];ids=(0,0,0,1,1,2,3,2,4,2,2)
            for p,n in zip(ps,ids):make_frame(p,n)
            verify_frames(*ps)
            for i in (1,2,4,6,7,8,9,10):
                make_frame(ps[i],5 if i not in (6,8) else 2)
                with self.assertRaises(ValueError):verify_frames(*ps)
                make_frame(ps[i],ids[i])
if __name__=='__main__':unittest.main()
