"""Independent synthetic description viewport, source-change and FAT proof."""
from pathlib import Path
import struct,sys,zlib
from c260_fat_slot_gate import valid_resume_slots,valid_slots
from c403_synthetic_descriptions import description
from c306_synthetic_texture_frame_gate import frame_rgb

def verify_fat(root,phase):
    spec={'last':(0,1,2,False),'short':(1,1,0,False),'empty':(2,0,0,False),'changed':(0,1,0,True)}
    if phase not in spec:raise ValueError('unknown phase')
    species,valid,page,changed=spec[phase];root=Path(root)
    r=valid_resume_slots(root);s=valid_slots(root,'pokedex3d',b'P3SV',64,60)
    if r[4]!=8 or r[12:14]!=bytes((0,1)) or r[76:79]!=bytes((5,valid,page)):
        raise ValueError('exact Description checkpoint not restored')
    if any(struct.unpack_from('<H',b,at)[0]!=species for b,at in ((s,12),(r,16),(r,20))):
        raise ValueError('description species selection differs')
    expected=zlib.crc32(description(species,changed).encode()) if valid else 0
    if struct.unpack_from('<I',r,80)[0]!=expected or struct.unpack_from('<H',r,24)[0]:
        raise ValueError('description source fingerprint or form differs')
    if s[16]!=1 or struct.unpack_from('<H',s,20)[0]!=0:
        raise ValueError('description browsing changed favorites')
    return {'phase':phase,'page':page,'text_bound':True,'favorites_unchanged':True}

def verify_frames(*paths):
    if len(paths)!=11:raise ValueError('eleven frames required')
    fs=[frame_rgb(p) for p in paths]
    if any(f[:2]!=(256,403) for f in fs):raise ValueError('wrong capture shape')
    def delta(a,b):
        return sum(fs[a][2](x,y)!=fs[b][2](x,y) for y in range(283,403) for x in range(8,248))
    for a,b in ((0,1),(1,2),(0,6),(6,8),(2,10)):
        if delta(a,b)<20:raise ValueError('page/species/source transition missing')
    for a,b in ((2,3),(2,4),(0,5),(6,7),(8,9)):
        if delta(a,b):raise ValueError('page clamp/previous/reboot differs')
    for row in (299,315,331,347):
        if sum(all(c>120 for c in fs[2][2](x,y)) for y in range(row,row+8) for x in range(8,128))<20:
            raise ValueError('last description page lost a source line')
    if sum(all(c>120 for c in fs[10][2](x,y)) for y in range(283,291) for x in range(80,224))<20:
        raise ValueError('changed text reset notice absent')
    return {'all_description_pages':True,'exact_resume':True,'changed_source_reset':True,'original_source_fidelity_verified':False}

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--fat':print('C403 FAT:',verify_fat(sys.argv[2],sys.argv[3]))
    else:print('C403 actual description:',verify_frames(*sys.argv[1:]))
