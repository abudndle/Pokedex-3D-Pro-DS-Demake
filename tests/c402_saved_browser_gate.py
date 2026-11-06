"""Public synthetic saved-list names, paging, FAT and reboot acceptance."""
from pathlib import Path
import struct,sys
from c260_fat_slot_gate import valid_slots,valid_resume_slots
from c306_synthetic_texture_frame_gate import frame_rgb

def verify_fat(root,phase):
    if phase not in ('recent','favorite','removed'):raise ValueError('unknown phase')
    root=Path(root);s=valid_slots(root,'pokedex3d',b'P3SV',64,60);r=valid_resume_slots(root)
    records=valid_slots(root,'pokedex3d_records',b'P3RC',160,156)
    ids=(0,1,3,4,5) if phase=='removed' else (0,1,2,3,4,5)
    if s[4]!=1 or s[16]!=len(ids) or struct.unpack_from('<'+str(len(ids))+'H',s,20)!=ids:
        raise ValueError('saved browser changed the wrong favorites')
    species=0 if phase=='recent' else 5
    if r[4]!=3 or r[12]!=0 or r[13]!=(5 if phase=='removed' else 1):
        raise ValueError('saved browser opened the wrong page or context')
    if any(struct.unpack_from('<H',buf,at)[0]!=species for buf,at in ((s,12),(r,16),(r,20))):
        raise ValueError('saved selection did not synchronize')
    if struct.unpack_from('<H',r,24)[0] or r[27]!=0:
        raise ValueError('stale form or MRU cursor')
    if phase!='recent' and r[62]!=(2 if phase=='removed' else 5):
        raise ValueError('favorite cursor did not persist')
    if records[16:98]!=bytes((255,))+bytes(81) or struct.unpack_from('<H',records,100)[0]!=species:
        raise ValueError('viewed inventory or recent head differs')
    return {'phase':phase,'favorites':ids,'selected_species':species,'resume_verified':True}

def verify_frames(*paths):
    if len(paths)!=11:raise ValueError('eleven frames required')
    fs=[frame_rgb(p) for p in paths]
    if any(f[:2]!=(256,403) for f in fs):raise ValueError('unexpected capture shape')
    def white(i,x,y):return all(c>120 for c in fs[i][2](x,y))
    def delta(a,b):
        return sum(fs[a][2](x,y)!=fs[b][2](x,y) for y in range(275,403) for x in range(8,248))
    for i,count in ((0,5),(1,3),(4,6),(8,5)):
        for row in range(count):
            # This is beyond numeric fallback labels: require long fixture names.
            if sum(white(i,x,y) for y in range(299+row*16,307+row*16) for x in range(136,232))<20:
                raise ValueError('saved entry source-name row missing or overwritten')
    if delta(0,1)<30:raise ValueError('Recent second page did not appear')
    if delta(4,7)<1:raise ValueError('Up/Down favorite cursor did not move')
    if delta(7,8)<30:raise ValueError('middle favorite removal did not update roster')
    for a,b in ((2,3),(5,6),(8,9),(8,10)):
        if delta(a,b):raise ValueError('open/reboot/empty-row tap changed expected view')
    return {'six_named_favorites':True,'recent_paging_and_touch':True,'removal_and_resume':True,'original_source_fidelity_verified':False}

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--fat':print('C402 FAT:',verify_fat(sys.argv[2],sys.argv[3]))
    else:print('C402 actual saved browser:',verify_frames(*sys.argv[1:]))
