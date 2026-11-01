"""C170: verify byte-level C5 descriptor spans without guessing primitive encoding.

All outputs are aggregate statistics; original bytes and per-model offsets stay private.
"""
import argparse
import json
import struct
import zipfile
from collections import Counter
from pathlib import Path
from c160_draw_pass_contract import parse_draws

def inspect(raw):
    n,_=parse_draws(raw)
    vstart,istart=struct.unpack_from("<2I",raw,0x3c)
    rows=[]
    for mesh in range(n):
        vo,_,vpacked,_,_=struct.unpack_from("<5I",raw,vstart+20*mesh)
        io,_,ipacked=struct.unpack_from("<3I",raw,istart+12*mesh)
        vc,ic=vpacked&65535,ipacked&65535
        if not vc or not ic or vo>=len(raw) or io>=len(raw):
            raise ValueError("descriptor offset/count outside source")
        if io+2*ic>len(raw):
            raise ValueError("candidate u16 span exceeds source")
        rows.append((vo,io,vc,ic,ipacked>>16))
    return rows

def audit(root):
    counts=Counter()
    seen=set()
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as z:
            for name in z.namelist():
                if not name.startswith("decoded_c5/") or not name.endswith(".c5"):continue
                mid=Path(name).stem
                if mid in seen:raise ValueError("duplicate source model")
                seen.add(mid)
                rows=inspect(z.read(name))
                counts["meshes"]+=len(rows)
                for vo,io,vc,ic,encoding in rows:
                    counts["same_vertex_index_offset"]+=vo==io
                    counts["index_offset_before_vertex"]+=io<vo
                    counts["index_offset_after_vertex"]+=io>vo
                    counts["candidate_triangle_multiple"]+=ic%3==0
                    counts["index_descriptor_tag_"+str(encoding)]+=1
    expected={f"p{i:03d}" for i in range(734) if i not in (721,722,723,724)}
    if seen!=expected:raise ValueError("incomplete source roster")
    return {"schema":"p3d-c170-geometry-layout-evidence-v1",
            "models":len(seen),"counts":dict(sorted(counts.items())),
            "index_encoding_verified":False,"primitive_order_verified":False,
            "animation_playback_verified":False,"original_textures_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("private_archive_directory",type=Path)
    p.add_argument("private_report",type=Path)
    a=p.parse_args()
    result=audit(a.private_archive_directory)
    a.private_report.parent.mkdir(parents=True,exist_ok=True)
    a.private_report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
