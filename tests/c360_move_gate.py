"""Independent synthetic Move Dex touch transition and FAT checkpoint gate."""
from pathlib import Path
import struct,sys
from c260_fat_slot_gate import valid_resume_slots
from c254_melonds_nav_gate import frame
def verify_fat(root):
    b=valid_resume_slots(Path(root))
    if (b[4]!=3 or b[12:14]!=bytes((0,3)) or b[28]!=0
            or struct.unpack_from('<H',b,18)[0]!=1
            or struct.unpack_from('<H',b,32)[0]!=0):
        raise ValueError('touch move selection retained stale text checkpoint')
    return {'move_index':1,'text_offset':0,'field':'description'}
def verify_frames(*paths):
    if len(paths)!=5:raise ValueError('five captures required')
    fs=[frame(p) for p in paths]
    if fs[0][:2]!=(256,403) or any(f[:4]!=fs[0][:4] for f in fs):raise ValueError('bad geometry')
    _,_,row,stride=fs[0][:4]
    def delta(a,b):
        return sum(fs[a][4][y*row+x*stride:y*row+x*stride+3]!=fs[b][4][y*row+x*stride:y*row+x*stride+3]
                   for y in range(275,391,2) for x in range(8,248,2))
    if delta(0,2)<15:raise ValueError('long original-field viewport did not scroll')
    if delta(0,1)<20:raise ValueError('short reference did not open')
    if delta(1,3)>15 or delta(1,4)>15:raise ValueError('touch or restart did not restore short text from beginning')
    return {'touch_short_text_matches_keypad':True,'resume_viewport':True,'original_data_verified':False}
if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--fat':print('C360 FAT:',verify_fat(sys.argv[2]))
    else:print('C360 actual move text transition:',verify_frames(*sys.argv[1:]))
