"""C169: investigate C5 descriptor payloads as possible float vertex records.

The index-table label is not proof that payload bytes encode indices.
Sample 32-bit finite floats and classify evidence; never certify primitives.
"""
import argparse
import json
import math
import struct
import zipfile
from pathlib import Path
from c160_draw_pass_contract import parse_draws

def inspect(raw):
    n,_=parse_draws(raw)
    istart=struct.unpack_from("<I",raw,0x40)[0]
    stats={"meshes":n,"float_finite_samples":0,"float_nontrivial_samples":0,
           "u16_index_incompatible":0}
    for mesh in range(n):
        offset,_,packed=struct.unpack_from("<3I",raw,istart+12*mesh)
        count=packed&65535
        vertex_count=struct.unpack_from("<I",raw,struct.unpack_from("<I",raw,0x3c)[0]+20*mesh+8)[0]&65535
        if not vertex_count or not count or offset>len(raw) or count>(len(raw)-offset)//2:
            raise ValueError("source payload bounds invalid")
        values=struct.unpack_from("<"+str(count)+"H",raw,offset)
        stats["u16_index_incompatible"]+=any(x>=vertex_count for x in values)
        sample=min(32,(count*2)//4)
        if sample:
            f=struct.unpack_from("<"+str(sample)+"f",raw,offset)
            if all(math.isfinite(x) for x in f):
                stats["float_finite_samples"]+=1
                if any(0.001<abs(x)<10000 for x in f):
                    stats["float_nontrivial_samples"]+=1
    return stats

def audit(root):
    total={"models":0,"meshes":0,"float_finite_samples":0,
           "float_nontrivial_samples":0,"u16_index_incompatible":0}
    roster=set()
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as z:
            for name in z.namelist():
                if not name.startswith("decoded_c5/") or not name.endswith(".c5"):continue
                mid=Path(name).stem
                if mid in roster:raise ValueError("duplicate model")
                roster.add(mid)
                result=inspect(z.read(name))
                total["models"]+=1
                for k in result:total[k]+=result[k]
    expected={f"p{i:03d}" for i in range(734) if i not in (721,722,723,724)}
    if roster!=expected:raise ValueError("incomplete source roster")
    return {"schema":"p3d-c169-descriptor-payload-evidence-v1",**total,
            "float_vertex_encoding_verified":False,"index_encoding_verified":False,
            "primitive_order_verified":False,"native_renderer_integrated":False}

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
