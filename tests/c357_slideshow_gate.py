"""Synthetic-only, independent actual-frame and FAT slideshow acceptance."""
from pathlib import Path
import struct
import sys
from c254_melonds_nav_gate import frame
from c260_fat_slot_gate import valid_resume_slots
from c355_album_view_gate import synthetic_photo


def verify_fat(root):
    root=Path(root);folder=root/'Pokedex 3D Pro'/'Photos'
    if {p.name for p in folder.iterdir()}!={f'AR_{n:04d}.png' for n in range(1,10)}:
        raise ValueError('photo roster changed')
    for n in range(1,10):
        if (folder/f'AR_{n:04d}.png').read_bytes()!=synthetic_photo(n):
            raise ValueError('slideshow modified a photo')
    data=valid_resume_slots(root)
    if data[4]!=3 or data[12:14]!=bytes((0,8)) or data[26]!=0:
        raise ValueError('B did not retain the final photo list selection')
    return {'media_unchanged':True,'final_list_selection':0}


def verify_frames(*paths):
    expected=(9,9,8,8,8,7,6,6,6,5,9,None)
    if len(paths)!=len(expected):raise ValueError('twelve captures required')
    frames=[frame(p) for p in paths]
    if frames[0][:2]!=(256,403) or any(f[:4]!=frames[0][:4] for f in frames):
        raise ValueError('slideshow geometry mismatch')
    def rgb(i,x,y):
        _,_,row,stride,pixels=frames[i]
        h=struct.unpack_from('>25I',Path(paths[i]).read_bytes())
        v=int.from_bytes(pixels[y*row+x*stride:y*row+(x+1)*stride],
                         'little' if h[7]==0 else 'big')
        out=[]
        for mask in h[14:17]:
            if not mask:raise ValueError('missing color mask')
            shift=(mask&-mask).bit_length()-1
            out.append(((v&mask)>>shift)*255//(mask>>shift))
        return tuple(out)
    for i,n in enumerate(expected[:-1]):
        color=tuple((c>>3)*255//31 for c in (n*17%256,n*29%256,n*41%256))
        for x,y in ((64,67),(128,115),(200,179)):
            if any(abs(a-b)>10 for a,b in zip(rgb(i,x,y),color)):
                raise ValueError(f'wrong timed/paused photo at capture {i}')
        if max(rgb(i,8,115))>8:raise ValueError('bad photo letterbox')
    color=tuple((c>>3)*255//31 for c in (9*17%256,9*29%256,9*41%256))
    if all(all(abs(a-b)<=10 for a,b in zip(rgb(11,x,y),color))
           for x,y in ((64,67),(128,115),(200,179))):
        raise ValueError('B did not close viewer')
    return {'timed_advance':True,'button_and_touch_pause_play':True,
            'manual_browse_pauses':True,'restart_paused':True,'oldest_to_newest_loop':True,
            'original_timing_verified':False,'hardware_verified':False}


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--fat':print('C357 FAT:',verify_fat(sys.argv[2]))
    else:print('C357 actual melonDS slideshow:',verify_frames(*sys.argv[1:]))
