"""Independent synthetic-photo FAT and real XWD viewer acceptance."""
from pathlib import Path
import struct
import sys
import zlib
from c260_fat_slot_gate import valid_resume_slots
from c268_fat_album_gate import check as check_roster
from c254_melonds_nav_gate import frame


def synthetic_photo(n):
    def chunk(t, b):
        return struct.pack('>I', len(b))+t+b+struct.pack('>I', zlib.crc32(t+b))
    rgb=bytes((n*17 % 256,n*29 % 256,n*41 % 256))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(b'\0'+rgb))+chunk(b'IEND',b''))


def verify_fat(root):
    root=Path(root)
    check_roster(root,tuple(f'AR_{n:04d}.png' for n in range(1,10)))
    for n in range(1,10):
        if (root/'Pokedex 3D Pro'/'Photos'/f'AR_{n:04d}.png').read_bytes()!=synthetic_photo(n):
            raise ValueError('viewing modified a photo')
    data=valid_resume_slots(root)
    if (data[4]!=3 or data[12:14]!=bytes((0,8)) or
            struct.unpack_from('<H',data,22)[0]!=0 or data[26]!=1):
        raise ValueError('Album selected photo was not retained')
    return {'all_nine_photos_unchanged':True,'album_selected':1}


def verify_frames(first,next_photo,returned,touched,reopened,listed,resumed):
    paths=(first,next_photo,returned,touched,reopened,listed,resumed)
    frames=[frame(p) for p in paths]
    if frames[0][:2]!=(256,403) or any(f[:4]!=frames[0][:4] for f in frames):
        raise ValueError('photo viewer XWD geometry mismatch')
    headers=[struct.unpack_from('>25I',Path(p).read_bytes()) for p in paths]
    def rgb(i,x,y):
        _,_,row,stride,pixels=frames[i]
        h=headers[i]
        value=int.from_bytes(pixels[y*row+x*stride:y*row+(x+1)*stride],
                             'little' if h[7]==0 else 'big')
        result=[]
        for mask in h[14:17]:
            if not mask:raise ValueError('missing XWD color mask')
            shift=(mask&-mask).bit_length()-1
            maximum=mask>>shift
            result.append(((value&mask)>>shift)*255//maximum)
        return tuple(result)
    def expected(n):
        return tuple(((c>>3)*255//31) for c in (n*17%256,n*29%256,n*41%256))
    for i,n in enumerate((9,8,9,8,8)):
        for x,y in ((64,67),(128,115),(200,179)):
            if any(abs(a-b)>10 for a,b in zip(rgb(i,x,y),expected(n))):
                raise ValueError(f'wrong decoded photo pixels in frame {i}')
        if max(rgb(i,8,115))>8:
            raise ValueError('photo letterbox was not black')
    def delta(a,b,box):
        x0,y0,x1,y1=box
        return sum(rgb(a,x,y)!=rgb(b,x,y) for y in range(y0,y1,4) for x in range(x0,x1,4))
    top=(32,19,224,211)
    if delta(0,1,top)<1000:raise ValueError('photo browsing did not change image')
    if delta(0,2,top) or delta(1,3,top) or delta(1,4,top):
        raise ValueError('keypad/touch/reopen selected different photo pixels')
    if sum(all(abs(a-b)<=10 for a,b in zip(rgb(5,x,y),expected(8)))
           for x,y in ((64,67),(128,115),(200,179)))>=2:
        raise ValueError('B did not close photo')
    if delta(5,6,(0,275,256,403))>15:
        raise ValueError('Album selection changed after reboot')
    return {'decoded_photo_colors_verified':True,'touch_keypad_browse_verified':True,
            'list_selection_restored':True,'original_asset_fidelity_verified':False,
            'dsi_camera_verified':False}


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--fat':
        print('C355 read-only photo and native selection checkpoint:',verify_fat(sys.argv[2]))
    elif len(sys.argv)==8:
        print('C355 real PNG photo viewer:',verify_frames(*sys.argv[1:]))
    else:raise SystemExit('usage: c355_album_view_gate.py --fat ROOT | FIRST NEXT RETURN TOUCH REOPEN LIST RESUMED')
