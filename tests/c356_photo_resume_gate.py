"""Independent synthetic FAT/checkpoint and actual melonDS photo-resume gate."""
from pathlib import Path
import struct
import sys
import zlib
from c260_fat_slot_gate import valid_resume_slots
from c355_album_view_gate import synthetic_photo
from c254_melonds_nav_gate import frame


def verify_fat(root, stage):
    root = Path(root)
    folder = root/'Pokedex 3D Pro'/'Photos'
    count = 9 if stage == 'saved' else 10
    if {p.name for p in folder.iterdir()} != {f'AR_{n:04d}.png' for n in range(1,count+1)}:
        raise ValueError('unexpected photo roster')
    for n in range(1,count+1):
        expected = synthetic_photo(7 if stage == 'changed' and n == 8 else n)
        if (folder/f'AR_{n:04d}.png').read_bytes() != expected:
            raise ValueError('photo bytes changed unexpectedly')
    data = valid_resume_slots(root)
    if data[12:14] != bytes((0,8)):
        raise ValueError('not in Album')
    if stage == 'changed':
        if data[4] != 3:
            raise ValueError('changed photo revived the viewer')
    else:
        original = synthetic_photo(8)
        if (data[4] != 7 or struct.unpack_from('<H',data,78)[0] != 8
                or struct.unpack_from('<II',data,80) != (zlib.crc32(original),len(original))
                or data[26] != (1 if stage == 'saved' else 2)):
            raise ValueError('wrong exact-photo checkpoint')
    return {'stage':stage,'photo_bytes_verified':True,'checkpoint_verified':True}


def verify_frames(*paths):
    if len(paths) != 4: raise ValueError('four captures required')
    frames = [frame(p) for p in paths]
    if frames[0][:2] != (256,403) or any(f[:4] != frames[0][:4] for f in frames):
        raise ValueError('wrong frame geometry')
    headers = [struct.unpack_from('>25I',Path(p).read_bytes()) for p in paths]
    def rgb(i,x,y):
        _,_,row,stride,pixels = frames[i]
        h = headers[i]
        v = int.from_bytes(pixels[y*row+x*stride:y*row+(x+1)*stride],
                           'little' if h[7] == 0 else 'big')
        out=[]
        for mask in h[14:17]:
            if not mask:raise ValueError('missing color mask')
            shift=(mask&-mask).bit_length()-1
            out.append(((v&mask)>>shift)*255//(mask>>shift))
        return tuple(out)
    expected = tuple((c>>3)*255//31 for c in (8*17%256,8*29%256,8*41%256))
    for i in range(3):
        for x,y in ((64,67),(128,115),(200,179)):
            if any(abs(a-b)>10 for a,b in zip(rgb(i,x,y),expected)):
                raise ValueError('wrong restored photo pixels')
        if max(rgb(i,8,115))>8:raise ValueError('wrong letterbox')
    if any(rgb(0,x,y)!=rgb(i,x,y) for i in (1,2)
           for y in range(19,211,4) for x in range(32,224,4)):
        raise ValueError('restored image changed')
    # A stale checkpoint must not display either its old image or replacement.
    for ident in (8,7):
        color=tuple((c>>3)*255//31 for c in (ident*17%256,ident*29%256,ident*41%256))
        if sum(all(abs(a-b)<=10 for a,b in zip(rgb(3,x,y),color))
               for x,y in ((64,67),(128,115),(200,179)))>=2:
            raise ValueError('changed photo displayed')
    return {'same_photo_after_reboot_and_roster_insert':True,'changed_photo_rejected':True,
            'original_asset_fidelity_verified':False,'hardware_verified':False}


if __name__ == '__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--fat':
        print('C356 FAT:',verify_fat(sys.argv[2],sys.argv[3]))
    elif len(sys.argv)==5:
        print('C356 melonDS:',verify_frames(*sys.argv[1:]))
    else:raise SystemExit('usage: --fat ROOT saved|reordered|changed | OPEN RESUME REORDERED CHANGED')
