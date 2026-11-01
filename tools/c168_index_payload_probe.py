"""C168: classify C5 index-descriptor payload evidence without guessing indices.

Descriptor fields name the original table, not a verified index encoding.
This probe identifies u16 incompatibility and possible float-like bytes only.
"""
import argparse
import json
import math
import struct
import zipfile
from pathlib import Path
from c160_draw_pass_contract import parse_draws

def probe(raw):
    meshes, _ = parse_draws(raw)
    vstart, istart = struct.unpack_from("<2I",raw,0x3c)
    incompatible = 0
    float_like = 0
    for mesh in range(meshes):
        vertex_descriptor=struct.unpack_from("<5I",raw,vstart+20*mesh)
        vertex_count=vertex_descriptor[2] & 65535
        offset, _, packed=struct.unpack_from("<3I",raw,istart+12*mesh)
        count=packed & 65535
        if not vertex_count or not count or offset > len(raw) or count > (len(raw)-offset)//2:
            raise ValueError("invalid source payload bounds")
        values=struct.unpack_from("<"+str(count)+"H",raw,offset)
        if any(v >= vertex_count for v in values):
            incompatible+=1
        sample_bytes=min(count*2,64)
        if sample_bytes >= 16:
            floats=struct.unpack_from("<"+str(sample_bytes//4)+"f",raw,offset)
            if all(math.isfinite(f) for f in floats) and any(0.001<abs(f)<10000 for f in floats):
                float_like+=1
    return {"mesh_descriptors":meshes,"u16_index_incompatible":incompatible,
            "float_like_sample_buffers":float_like,
            "index_encoding_verified":False,"geometry_order_verified":False}

def audit(root):
    total={"models":0,"mesh_descriptors":0,"u16_index_incompatible":0,
           "float_like_sample_buffers":0}
    roster=set()
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as z:
            for name in z.namelist():
                if not name.startswith("decoded_c5/") or not name.endswith(".c5"):continue
                mid=Path(name).stem
                if mid in roster:raise ValueError("duplicate model")
                roster.add(mid)
                data=probe(z.read(name))
                total["models"]+=1
                for key in ("mesh_descriptors","u16_index_incompatible","float_like_sample_buffers"):
                    total[key]+=data[key]
    expected={f"p{i:03d}" for i in range(734) if i not in (721,722,723,724)}
    if roster!=expected:raise ValueError("incomplete model roster")
    return {"schema":"p3d-c168-index-payload-probe-v1",**total,
            "index_encoding_verified":False,"geometry_order_verified":False,
            "native_renderer_integrated":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("private_archive_directory",type=Path)
    p.add_argument("private_output",type=Path)
    a=p.parse_args()
    result=audit(a.private_archive_directory)
    a.private_output.parent.mkdir(parents=True,exist_ok=True)
    a.private_output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
