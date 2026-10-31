#!/usr/bin/env python3
"""Validate original mesh descriptor-to-OBJ export counts, NOT materials.

Requires privately recovered C5 decoded archives and original C7 geometry ZIP.
No commercial assets are in this repository. Never derive P3MT bindings from
descriptor order or matching face counts: GPU material selection is unknown.
"""
import argparse
import csv
import json
import re
import struct
import zipfile
from collections import Counter
from pathlib import Path

C5_RE=re.compile(r"decoded_c5/(p\d{3})\.c5$")
OBJ_RE=re.compile(r"models/(p\d{3})\.obj$")
ROSTER={f"p{i:03d}" for i in range(734) if i not in (721,722,723,724)}

def obj_groups(raw):
    groups=[]
    seen=set()
    total=0
    global_vertices=0
    current=None
    for line in raw.splitlines():
        if line.startswith(b"o "):
            name=line[2:].decode("ascii").strip()
            if not name or name in seen:raise ValueError("duplicate or invalid OBJ mesh")
            seen.add(name)
            current={"name":name,"vertices":0,"faces":0}
            groups.append(current)
        elif line.startswith(b"v "):
            total+=1
            if current is None:global_vertices+=1
            else:current["vertices"]+=1
        elif line.startswith(b"f "):
            if current is None or len(line.split())!=4:raise ValueError("nontriangle or ungrouped OBJ face")
            current["faces"]+=1
    if not groups or not total or any(g["faces"]<=0 for g in groups):
        raise ValueError("incomplete OBJ mesh data")
    return groups,total,global_vertices

def descriptor_pairs(data):
    if len(data)<0x78 or data[:2]!=b"\xc5x":raise ValueError("invalid source C5")
    nv,ni=struct.unpack_from("<2H",data,0x14)
    vstart,istart,after=struct.unpack_from("<3I",data,0x3c)
    if not (0<nv<=1000 and ni==nv and 0x78<=vstart<=istart<=after<len(data)
            and istart-vstart==nv*20 and after-istart==ni*12):
        raise ValueError("bad C5 descriptor table lengths")
    result=[]
    for i in range(nv):
        vptr,reserved,packed,layout,flags=struct.unpack_from("<5I",data,vstart+i*20)
        count=packed&65535
        stride=(packed>>16)&255
        iptr,ireserved,ipacked=struct.unpack_from("<3I",data,istart+i*12)
        indices=ipacked&65535
        width=ipacked>>16
        if reserved or not count or not stride or vptr+count*stride>len(data):
            raise ValueError("invalid C5 vertex descriptor")
        if ireserved or not indices or indices%3 or width not in (2,4) or iptr+indices*width>len(data):
            raise ValueError("invalid C5 index descriptor")
        result.append({"vertices":count,"faces":indices//3,"stride":stride,
                       "index_width":width,"layout":layout,"flag":flags})
    return result

def audit(root):
    original={}
    with zipfile.ZipFile(root/"Pokedex3D_C7_Validated_Geometry_OBJ_Collection.zip") as z:
        for name in z.namelist():
            m=OBJ_RE.fullmatch(name)
            if m:
                if m.group(1) in original:raise ValueError("duplicate original OBJ")
                original[m.group(1)]=obj_groups(z.read(name))
    seen=set()
    mesh_rows=[]
    model_rows=[]
    errors=[]
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as z:
            for name in z.namelist():
                m=C5_RE.fullmatch(name)
                if not m:continue
                model=m.group(1)
                if model in seen:
                    errors.append(model+": duplicate C5")
                    continue
                seen.add(model)
                try:
                    descriptors=descriptor_pairs(z.read(name))
                    if model not in original:
                        model_rows.append({"model_id":model,"source_descriptors":len(descriptors),
                           "exported_groups":0,"matched":0,"status":"NO_C7_OBJ_EXPORT",
                           "issues":"source OBJ absent","verified_material_links":0})
                        continue
                    groups,total,global_vertices=original[model]
                    issues=[]
                    if len(groups)!=len(descriptors):issues.append("mesh descriptor group count mismatch")
                    if sum(d["vertices"] for d in descriptors)!=total:
                        issues.append("total source vertices differ")
                    matched=0
                    for i,d in enumerate(descriptors):
                        group=groups[i] if i<len(groups) else None
                        if group is None:
                            state="MISSING_ORIGINAL_OBJ_GROUP"
                            issues.append(f"mesh {i} not exported")
                        elif not group["name"].endswith(f"_mesh_{i}"):
                            raise ValueError(f"mesh {i} export order differs")
                        elif group["faces"]!=d["faces"]:
                            state="TRUNCATED_ORIGINAL_OBJ_FACES"
                            issues.append(f"mesh {i} original/exported faces differ")
                        elif not global_vertices and group["vertices"]!=d["vertices"]:
                            state="VERTEX_COUNT_MISMATCH"
                            issues.append(f"mesh {i} local vertex count differs")
                        else:
                            state="DESCRIPTOR_EXPORT_COUNTS_AND_ORDER_MATCH"
                            matched+=1
                        mesh_rows.append({"model_id":model,"mesh_index":i,
                            "mesh_name":group["name"] if group else f"{model}_mesh_{i}",
                            "source_vertices":d["vertices"],"source_faces":d["faces"],
                            "exported_vertices":group["vertices"] if group else 0,
                            "exported_faces":group["faces"] if group else 0,
                            "vertex_stride":d["stride"],"index_width":d["index_width"],
                            "geometry_layout":f"0x{d['layout']:08x}",
                            "source_mesh_status":state,
                            "original_material_id":"","original_texture_id":"",
                            "mesh_material_status":"UNVERIFIED"})
                    model_rows.append({"model_id":model,"source_descriptors":len(descriptors),
                        "exported_groups":len(groups),"matched":matched,
                        "status":"COUNTS_AND_ORDER_MATCH" if not issues else "INCOMPLETE_ORIGINAL_OBJ",
                        "issues":"; ".join(issues),"verified_material_links":0})
                except (ValueError,UnicodeError,struct.error) as exc:
                    errors.append(f"{model}: {exc}")
    if seen!=ROSTER:errors.append(f"expected 730 original models; found {len(seen)}")
    if set(original)-seen:errors.append("C7 OBJ model without original C5")
    statuses=Counter(r["status"] for r in model_rows)
    report={"milestone":"C89","original_model_files":len(seen),
      "original_geometry_exports":len(original),
      "descriptors_examined":len(mesh_rows),
      "descriptors_with_matching_export_counts":sum(r["source_mesh_status"]==
           "DESCRIPTOR_EXPORT_COUNTS_AND_ORDER_MATCH" for r in mesh_rows),
      "descriptors_incomplete":sum(r["source_mesh_status"]!=
           "DESCRIPTOR_EXPORT_COUNTS_AND_ORDER_MATCH" for r in mesh_rows),
      "incomplete_model_ids":[r["model_id"] for r in model_rows if r["status"]=="INCOMPLETE_ORIGINAL_OBJ"],
      "status_counts":dict(statuses),"verified_mesh_material_links":0,
      "verified_face_material_ranges":0,"errors":errors,
      "limitation":"Counts/order match only. C5 index payload topology and original mesh material references are not proven."}
    return mesh_rows,model_rows,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    mesh,models,report=audit(args.private_root)
    args.out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("C89_mesh_join.csv",mesh),("C89_model_queue.csv",models)):
        if rows:
            with (args.out/name).open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    (args.out/"C89_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return int(bool(report["errors"]))

if __name__=="__main__":
    raise SystemExit(main())
