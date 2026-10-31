#!/usr/bin/env python3
"""Audit original C5 draw-table mesh and material references (source-only).

Never emits P3MT diffuse bindings. Original texture sampler roles and the
complete source 3DS geometry still need independent verification.
"""
import argparse
import collections
import csv
import json
import re
import struct
import zipfile
from pathlib import Path

NAME = re.compile(r"decoded_c5/(p\d{3})\.c5$")
PASS_PRIMARY = 0x0c02
PASS_SECONDARY = 0x0c01
ROSTER = {f"p{i:03d}" for i in range(734) if i not in (721,722,723,724)}

def draws(data, model_id):
    if len(data)<120 or data[:2]!=b"\xc5x":
        raise ValueError("original decoded C5 header invalid")
    nmaterial=struct.unpack_from("<H",data,0x10)[0]
    nmesh,ni=struct.unpack_from("<2H",data,0x14)
    nrows=struct.unpack_from("<H",data,0x18)[0]
    vstart,istart,dstart=struct.unpack_from("<3I",data,0x3c)
    dend=struct.unpack_from("<I",data,0x50)[0]
    if not (0<nmaterial<=256 and 0<nmesh==ni and 0<nrows<=1024 and
            vstart>=120 and istart==vstart+20*nmesh and
            dstart==istart+12*ni and dend==dstart+40*nrows and dend<=len(data)):
        raise ValueError("original draw table layout/count mismatch")
    records=[]
    for row in range(nrows):
        packed,vertex,index,palette,faces,bones,offset,mode=struct.unpack_from(
            "<8H",data,dstart+40*row)
        material=packed&255
        if not (material<nmaterial and vertex<nmesh and index<ni and vertex==index
                and mode in (PASS_PRIMARY,PASS_SECONDARY) and faces>0):
            raise ValueError(f"draw {row}: original mesh/material reference outside C5 tables")
        count=struct.unpack_from("<I",data,istart+index*12+8)[0]&0xffff
        if faces*3!=count:
            raise ValueError(f"draw {row}: source face count mismatch")
        records.append({
            "model_id":model_id,"draw_index":row,"pass_code":f"0x{mode:04x}",
            "mesh_index":vertex,"material_index":material,"triangle_count":faces,
            "source_material_status":"VERIFIED_C5_DRAW_TABLE",
            "color_texture_slot":"UNVERIFIED"})
    return records,nmesh

def primary_map(rows,nmesh):
    by_mesh=collections.defaultdict(set)
    for r in rows:
        if r["pass_code"]=="0x0c02":
            by_mesh[r["mesh_index"]].add(r["material_index"])
    unique={i:next(iter(by_mesh[i])) for i in range(nmesh) if len(by_mesh[i])==1}
    unresolved=[i for i in range(nmesh) if len(by_mesh[i])!=1]
    return unique,unresolved

def audit(root):
    roster=set()
    records=[]
    model_rows=[]
    errors=[]
    for part in (1,2,3):
        archive=root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
        with zipfile.ZipFile(archive) as z:
            for filename in z.namelist():
                m=NAME.fullmatch(filename)
                if not m:continue
                mid=m.group(1)
                if mid in roster:
                    errors.append(mid+": duplicate original model")
                    continue
                roster.add(mid)
                try:
                    rows,nmesh=draws(z.read(filename),mid)
                    mapping,unresolved=primary_map(rows,nmesh)
                except (ValueError,struct.error) as exc:
                    errors.append(mid+": "+str(exc))
                    continue
                records.extend(rows)
                model_rows.append({"model_id":mid,"source_meshes":nmesh,
                    "original_draws":len(rows),"unique_primary_mesh_materials":len(mapping),
                    "unresolved_primary_meshes":",".join(map(str,unresolved)),
                    "verified_diffuse_sampler_slots":0})
    if roster!=ROSTER:errors.append("C5 roster missing or has unexpected model IDs")
    passes=collections.Counter(r["pass_code"] for r in records)
    report={"original_models":len(roster),"original_draw_material_links":len(records),
        "primary_draw_rows":passes["0x0c02"],"secondary_draw_rows":passes["0x0c01"],
        "models_with_unresolved_primary_mesh_refs":sum(bool(x["unresolved_primary_meshes"]) for x in model_rows),
        "unresolved_model_ids":[x["model_id"] for x in model_rows if x["unresolved_primary_meshes"]],
        "verified_diffuse_sampler_slots":0,
        "generated_p3mt_diffuse_bindings":0,"errors":errors}
    return records,model_rows,report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private-root",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    records,models,report=audit(a.private_root)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    if records:
        for filename,rows in (("C90_draw_materials.csv",records),("C90_model_status.csv",models)):
            with (a.output_dir/filename).open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
    (a.output_dir/"C90_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return bool(report["errors"])
if __name__=="__main__":
    raise SystemExit(main())
