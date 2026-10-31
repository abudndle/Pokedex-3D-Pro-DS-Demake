#!/usr/bin/env python3
"""C94: validate recovered UV OBJ geometry against its source C7 OBJ export.

Source vertex/triangle order must be EXACTLY preserved; never infer original
3DS GPU UV semantics or sampler-channel assignments from a passing audit.
This script contains no game assets; user-provided sources remain private.
"""
import argparse
import json
import math
import zipfile
from pathlib import Path

def read_topology(raw, require_uv):
    vertices=[];meshes=[];faces=[];tex=[]
    for line in raw.splitlines():
        if line.startswith(b'v '):
            coords=line[2:].split()
            if len(coords)!=3 or any(not math.isfinite(float(x)) for x in coords):
                raise ValueError("invalid source XYZ")
            vertices.append(line.strip())
        elif line.startswith(b'vt '):
            coords=line[3:].split()
            if len(coords)!=2 or any(not math.isfinite(float(x)) or abs(float(x))>7.99 for x in coords):
                raise ValueError("UV outside signed DS preview range")
            tex.append(line.strip())
        elif line.startswith(b'o '):
            meshes.append(line.strip())
        elif line.startswith(b'f '):
            terms=line[2:].split()
            if not meshes or len(terms)!=3:
                raise ValueError("source mesh is not grouped triangles")
            row=[]
            for term in terms:
                parts=term.split(b'/')
                vertex=int(parts[0])
                if not 1<=vertex<=len(vertices):raise ValueError("invalid source vertex index")
                if require_uv:
                    if len(parts)<2 or not parts[1]:
                        raise ValueError("original-derived UV missing")
                    ti=int(parts[1])
                    if not 1<=ti<=len(tex):raise ValueError("invalid source UV index")
                row.append(vertex)
            faces.append(tuple(row))
    if not vertices or not meshes or not faces or len(faces)>16000:
        raise ValueError("empty or oversized recovered OBJ")
    if require_uv and not tex:raise ValueError("source UV table missing")
    return tuple(vertices),tuple(meshes),tuple(faces)

def validate_pair(source_c7, recovered_uv):
    original=read_topology(source_c7,False)
    recovered=read_topology(recovered_uv,True)
    if recovered!=original:
        raise ValueError("source UV reconstruction changed vertex, group or face order")
    return {"faces":len(original[2]),"mesh_groups":len(original[1]),
            "verified_original_C7_geometry_order":True,
            "original_3ds_sampler_channels_verified":False}

def audit(c7, c62, model_ids):
    complete={};errors={}
    with zipfile.ZipFile(c7) as source,zipfile.ZipFile(c62) as uv:
        uv_members=set(uv.namelist())
        for model in model_ids:
            try:
                original=source.read("models/"+model+".obj")
                alternate="C62/"+model+".obj"
                uv_bytes=uv.read(alternate) if alternate in uv_members else original
                item=validate_pair(original,uv_bytes)
                item["uv_source"]="C62" if alternate in uv_members else "C7"
                complete[model]=item
            except (KeyError,ValueError,UnicodeError) as exc:
                errors[model]=str(exc)
    return {"models_checked":len(model_ids),"full_obj_pairs_verified":len(complete),
            "source_triangle_count":sum(r["faces"] for r in complete.values()),
            "source_c62_uv_models":sum(r["uv_source"]=="C62" for r in complete.values()),
            "source_c7_uv_models":sum(r["uv_source"]=="C7" for r in complete.values()),
            "gpu_sampler_roles_verified":False,"failures":errors}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-c7",type=Path,required=True)
    p.add_argument("--recovered-c62",type=Path,required=True)
    p.add_argument("--model-ids",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ids=json.loads(a.model_ids.read_text(encoding="utf8"))
    if not isinstance(ids,list) or len(ids)!=len(set(ids)) or any(
        not isinstance(x,str) or len(x)!=4 or not x.startswith("p") or not x[1:].isdigit()
        for x in ids):
        p.error("invalid or duplicate original model IDs")
    result=audit(a.original_c7,a.recovered_c62,ids)
    a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in result.items() if k!="failures"},indent=2))
    return int(bool(result["failures"]))

if __name__=="__main__":
    raise SystemExit(main())
