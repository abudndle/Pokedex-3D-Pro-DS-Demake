from pathlib import Path
import struct,tempfile,unittest,zlib
from c403_description_gate import verify_fat,verify_frames
from c403_synthetic_descriptions import description

def fixture_frame(p,phase,lines=4,notice=False):
    h=[0]*25;h[0:4]=[100,7,2,24];h[4:6]=[256,403];h[11:13]=[32,1024];h[14:17]=[0xff0000,0xff00,0xff]
    raw=bytearray(256*403*4)
    for line in range(lines):
        for y in range(299+line*16,307+line*16):
            for x in range(8,128):raw[(y*256+x)*4:(y*256+x)*4+3]=b'\xff'*3
    for y in range(292,298):
        for x in range(16,80):raw[(y*256+x)*4]=phase*20
    if notice:
        for y in range(283,291):
            for x in range(80,224):raw[(y*256+x)*4:(y*256+x)*4+3]=b'\xff'*3
    p.write_bytes(struct.pack('>25I',*h)+raw)

class DescriptionGateTests(unittest.TestCase):
    def test_exact_fields_and_strict_v8_shape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for phase,species,valid,page,changed in [('last',0,1,2,False),('short',1,1,0,False),('empty',2,0,0,False),('changed',0,1,0,True)]:
                s=bytearray(64);s[:5]=b'P3SV\x01';s[16]=1
                r=bytearray(96);r[:5]=b'P3RV\x08';r[13]=1;r[76:79]=bytes((5,valid,page))
                for b,at in ((s,12),(r,16),(r,20)):struct.pack_into('<H',b,at,species)
                crc=zlib.crc32(description(species,changed).encode()) if valid else 0
                struct.pack_into('<I',r,80,crc)
                def save():
                    for name,b in [('pokedex3d',s),('pokedex3d_resume',r)]:
                        struct.pack_into('<I',b,len(b)-4,zlib.crc32(b[:-4]));(root/(name+'_A.sav')).write_bytes(b)
                save();verify_fat(root,phase)
                for b,at in ((s,16),(s,20),(s,12),(r,4),(r,13),(r,16),(r,20),(r,24),(r,76),(r,77),(r,78),(r,79),(r,80),(r,84)):
                    b[at]^=1;save()
                    with self.assertRaises(ValueError):verify_fat(root,phase)
                    b[at]^=1
    def test_frames_reject_missing_pages_lines_notice_and_restart(self):
        with tempfile.TemporaryDirectory() as d:
            ps=[Path(d)/f'{i}.xwd' for i in range(11)]
            phases=(0,1,2,2,2,0,3,3,4,4,5);counts=(4,4,4,4,4,4,1,1,0,0,4)
            for i,(p,n,c) in enumerate(zip(ps,phases,counts)):fixture_frame(p,n,c,i==10)
            verify_frames(*ps)
            for i,n,c,notice in ((1,0,4,False),(4,6,4,False),(2,2,3,False),(10,5,4,False)):
                fixture_frame(ps[i],n,c,notice)
                with self.assertRaises(ValueError):verify_frames(*ps)
                fixture_frame(ps[i],phases[i],counts[i],i==10)
if __name__=='__main__':unittest.main()
