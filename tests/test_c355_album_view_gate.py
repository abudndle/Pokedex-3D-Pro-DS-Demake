from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from c355_album_view_gate import synthetic_photo,verify_fat,verify_frames


def capture(path,ident=None):
    h=[0]*25
    h[0:6]=[100,7,2,24,256,403]
    h[7]=0;h[11]=32;h[12]=1024
    h[14:17]=[0xff0000,0xff00,0xff]
    pixels=bytearray(256*403*4)
    def paint(x0,y0,x1,y1,rgb):
        r,g,b=rgb
        for y in range(y0,y1):
            for x in range(x0,x1):
                pos=(y*256+x)*4;pixels[pos:pos+4]=bytes((b,g,r,255))
    paint(0,0,256,19,(50,50,50))
    paint(0,211,256,403,(20,20,20))
    paint(10,285,190,365,(150,150,150))
    if ident:
        rgb=tuple((c>>3)*255//31 for c in (ident*17%256,ident*29%256,ident*41%256))
        paint(32,19,224,211,rgb)
    else:paint(20,50,180,120,(90,90,90))
    path.write_bytes(struct.pack('>25I',*h)+pixels)


class ViewerGateTests(unittest.TestCase):
    def test_real_frame_contract_and_wrong_views(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/f'{i}.xwd' for i in range(7)]
            ids=[9,8,9,8,8,None,None]
            for p,n in zip(paths,ids):capture(p,n)
            self.assertTrue(verify_frames(*paths)['decoded_photo_colors_verified'])
            for i in range(5):
                capture(paths[i],8 if ids[i]==9 else 9)
                with self.assertRaises(ValueError):verify_frames(*paths)
                capture(paths[i],ids[i])
            capture(paths[5],8)
            with self.assertRaisesRegex(ValueError,'B did not'):verify_frames(*paths)
            capture(paths[5],None);capture(paths[6],9)
            # A wrong/blank DS screen cannot replace a resumed list.
            data=bytearray(paths[6].read_bytes())
            data[100+300*1024:100+350*1024]=b'\0'*(50*1024)
            paths[6].write_bytes(data)
            with self.assertRaises(ValueError):verify_frames(*paths)

    def test_fat_checkpoint_and_photo_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/'Pokedex 3D Pro'/'Photos';folder.mkdir(parents=True)
            for n in range(1,10):(folder/f'AR_{n:04d}.png').write_bytes(synthetic_photo(n))
            b=bytearray(80);b[:5]=b'P3RV\x03';b[13]=8;b[26]=1
            def save():
                struct.pack_into('<I',b,76,zlib.crc32(b[:76]))
                (root/'pokedex3d_resume_A.sav').write_bytes(b)
            save();self.assertTrue(verify_fat(root)['all_nine_photos_unchanged'])
            b[26]=0;save()
            with self.assertRaisesRegex(ValueError,'selected photo'):verify_fat(root)
            b[26]=1;save();(folder/'AR_0008.png').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'modified a photo'):verify_fat(root)


if __name__=='__main__':unittest.main()
