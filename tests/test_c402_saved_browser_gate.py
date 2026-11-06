from pathlib import Path
import struct,tempfile,unittest,zlib
from c402_saved_browser_gate import verify_fat,verify_frames

def fixture_frame(p,n,count):
    h=[0]*25;h[0:4]=[100,7,2,24];h[4:6]=[256,403];h[11:13]=[32,1024];h[14:17]=[0xff0000,0xff00,0xff]
    raw=bytearray(256*403*4)
    for row in range(count):
        for y in range(299+row*16,307+row*16):
            for x in range(136,201):raw[(y*256+x)*4:(y*256+x)*4+3]=b'\xff'*3
    for y in range(280,296):
        for x in range(16,32):raw[(y*256+x)*4]=n*20
    p.write_bytes(struct.pack('>25I',*h)+raw)

class BrowserGateTests(unittest.TestCase):
    def test_fat_selection_removal_and_cursor(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for phase in ('recent','favorite','removed'):
                s=bytearray(64);s[:5]=b'P3SV\x01';r=bytearray(80);r[:5]=b'P3RV\x03'
                c=bytearray(160);c[:5]=b'P3RC\x01';c[16]=255
                ids=(0,1,3,4,5) if phase=='removed' else (0,1,2,3,4,5)
                s[16]=len(ids);struct.pack_into('<'+str(len(ids))+'H',s,20,*ids)
                species=0 if phase=='recent' else 5
                for b,at in ((s,12),(r,16),(r,20),(c,100)):struct.pack_into('<H',b,at,species)
                r[13]=5 if phase=='removed' else 1;r[62]=2 if phase=='removed' else 5 if phase=='favorite' else 0
                def save():
                    for name,b in [('pokedex3d',s),('pokedex3d_resume',r),('pokedex3d_records',c)]:
                        struct.pack_into('<I',b,len(b)-4,zlib.crc32(b[:-4]));(root/(name+'_A.sav')).write_bytes(b)
                save();verify_fat(root,phase)
                for b,at in ((s,16),(s,20),(s,12),(r,13),(r,16),(r,20),(r,24),(r,27),(c,16),(c,100)):
                    b[at]^=1;save()
                    with self.assertRaises(ValueError):verify_fat(root,phase)
                    b[at]^=1
                if phase!='recent':
                    r[62]^=1;save()
                    with self.assertRaises(ValueError):verify_fat(root,phase)
    def test_frames_reject_missing_names_wrong_touch_and_stale_reboot(self):
        with tempfile.TemporaryDirectory() as d:
            ps=[Path(d)/f'{i}.xwd' for i in range(11)]
            ids=(0,1,2,2,3,4,4,5,6,6,6);counts=(5,3,0,0,6,0,0,6,5,5,5)
            for p,n,c in zip(ps,ids,counts):fixture_frame(p,n,c)
            verify_frames(*ps)
            for i,n,c in ((4,3,5),(3,7,0),(9,7,5),(10,7,5)):
                fixture_frame(ps[i],n,c)
                with self.assertRaises(ValueError):verify_frames(*ps)
                fixture_frame(ps[i],ids[i],counts[i])
if __name__=='__main__':unittest.main()
