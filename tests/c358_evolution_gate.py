"""Independent synthetic FAT and actual melonDS evolution-flow acceptance."""
from pathlib import Path
import struct
import sys
from c260_fat_slot_gate import valid_resume_slots
from c254_melonds_nav_gate import frame


def verify_fat(root,target):
    b=valid_resume_slots(Path(root))
    if (b[4]!=5 or b[12:14]!=bytes((0,1)) or b[76]!=3
            or struct.unpack_from('<H',b,16)[0]!=target
            or struct.unpack_from('<H',b,20)[0]!=target
            or struct.unpack_from('<H',b,24)[0]!=0):
        raise ValueError('wrong evolution target/form/detail checkpoint')
    return {'species_index':target,'selected_species_index':target,'form':0,'tab':3}


def verify_frames(*paths):
    if len(paths)!=8:raise ValueError('eight captures required')
    frames=[frame(p) for p in paths]
    if frames[0][:2]!=(256,403) or any(f[:4]!=frames[0][:4] for f in frames):
        raise ValueError('inconsistent DS evolution capture geometry')
    _,_,row,stride=frames[0][:4]
    def delta(a,b):
        pa,pb=frames[a][4],frames[b][4]
        return sum(pa[y*row+x*stride:y*row+x*stride+3]!=
                   pb[y*row+x*stride:y*row+x*stride+3]
                   for y in range(275,391,2) for x in range(8,248,2))
    # Reject blank/flat captures even if all reboot copies match.
    for f in frames:
        pixels=f[4]
        colors={pixels[y*row+x*stride:y*row+x*stride+3]
                for y in range(275,391,2) for x in range(8,248,2)}
        if len(colors)<2:raise ValueError('empty evolution screen')
    if delta(0,1)<40 or delta(1,5)<40:
        raise ValueError('evolution target or missing-data screen did not change')
    for a,b in ((0,4),(1,2),(1,3),(5,6),(5,7)):
        if delta(a,b)>15:
            raise ValueError('empty-row tap, source return or reboot changed the screen')
    return {'both_branches_navigated':True,'terminal_and_missing_rows_inert':True,
            'detail_resume':True,'original_data_verified':False,'hardware_verified':False}


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--fat':
        print('C358 FAT:',verify_fat(sys.argv[2],int(sys.argv[3])))
    else:print('C358 actual melonDS evolution flow:',verify_frames(*sys.argv[1:]))
