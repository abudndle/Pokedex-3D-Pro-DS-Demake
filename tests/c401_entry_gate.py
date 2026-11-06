"""Synthetic entry handoff: genuine FAT records and emulator frames."""
from pathlib import Path
import struct,sys
from c260_fat_slot_gate import valid_slots,valid_resume_slots
from c254_melonds_nav_gate import frame

def verify_fat(root,phase):
    s=valid_slots(Path(root),'pokedex3d',b'P3SV',64,60)
    r=valid_resume_slots(Path(root))
    if s[4]!=1 or s[16]!=1 or struct.unpack_from('<H',s,20)[0]!=0:
        raise ValueError('entry opening changed the single original favorite')
    if phase not in ('favorite','recent','scroll','move','effect'):raise ValueError('unknown phase')
    species=0 if phase=='favorite' else 1
    if struct.unpack_from('<H',s,12)[0]!=species:raise ValueError('progress species not synchronized')
    if r[4]!=3 or r[12]!=0 or struct.unpack_from('<H',r,16)[0]!=species or struct.unpack_from('<H',r,20)[0]!=species:
        raise ValueError('entry selection or default tab not synchronized')
    if struct.unpack_from('<H',r,24)[0]!=0:raise ValueError('stale alternate form')
    move=phase in ('scroll','move','effect')
    if r[13]!=(3 if move else 1):raise ValueError('entry did not open its destination page')
    if move:
        offset=struct.unpack_from('<H',r,32)[0]
        if struct.unpack_from('<H',r,18)[0]!=0 or r[28]!=(phase=='effect'):
            raise ValueError('move identity or field did not reset')
        if (phase=='scroll' and offset==0) or (phase!='scroll' and offset!=0):
            raise ValueError('move viewport setup or reset failed')
    return {'phase':phase,'favorites_unchanged':True,'selection_synchronized':True}

def verify_frames(*paths):
    if len(paths)!=11:raise ValueError('eleven captures required')
    fs=[frame(p) for p in paths]
    if fs[0][:2]!=(256,403) or any(f[:4]!=fs[0][:4] for f in fs):raise ValueError('bad frame geometry')
    _,_,row,stride=fs[0][:4]
    def delta(a,b):
        return sum(fs[a][4][y*row+x*stride:y*row+x*stride+3]!=fs[b][4][y*row+x*stride:y*row+x*stride+3]
                   for y in range(275,391,2) for x in range(8,248,2))
    for a,b in ((0,1),(0,2),(3,4),(5,7),(5,9),(5,10)):
        if delta(a,b)>15:raise ValueError('entry or restart did not match its clean reference')
    # Pokemon 001 -> 002 changes one small number glyph. Require a real
    # digit change in its exact visible field; FAT independently proves ID 1.
    digit_change=sum(fs[0][4][y*row+x*stride:y*row+x*stride+3]!=fs[3][4][y*row+x*stride:y*row+x*stride+3]
                     for y in range(315,323) for x in range(72,96))
    if digit_change==0:raise ValueError('recent entry species-number glyph did not change')
    for a,b in ((5,6),(5,8)):
        if delta(a,b)<15:raise ValueError('scenario did not establish a distinct viewport/field')
    return {'favorite_and_recent_open_verified':True,'same_move_reset_verified':True,'original_game_parity_verified':False}

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--fat':print('C401 FAT:',verify_fat(sys.argv[2],sys.argv[3]))
    else:print('C401 actual entry frames:',verify_frames(*sys.argv[1:]))
