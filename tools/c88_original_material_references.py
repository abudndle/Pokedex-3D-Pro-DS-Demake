#!/usr/bin/env python3
"""Audit original C5 material->shader and texture index links, never mesh faces.

Requires the user's private decoded C56 and C75 reference CSV. No original
Nintendo model/textures are bundled or generated. A record is NOT P3MT.
"""
import argparse
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import re
import struct
import zipfile

C5_NAME=re.compile(r"decoded_c5/(p\d{3})\.c5$")
FIELDS=("model_id","material_index","source_material_name","source_shader_index",
        "shader_name","texture_index0","texture_index1","texture_name0",
        "texture_name1","source_reference_status","mesh_material_binding")

def name_at(data,offset,limit):
    if not 0<=offset<limit:raise ValueError("C5 string offset out of bounds")
    end=data.find(b"\0",offset,min(limit,offset+128))
    if end<=offset:raise ValueError("unterminated original C5 string")
    raw=data[offset:end]
    if any(c<32 or c>126 for c in raw):raise ValueError("invalid C5 string")
    return raw.decode("ascii")

def parse(data,textures):
    if data[:2]!=b"\xc5x" or len(data)<120:raise ValueError("not a decoded C5")
    nshader,ntex,nmaterial=struct.unpack_from("<3H",data,0x0c)
    shader_start,tex_start,material_start,bone_start=struct.unpack_from("<4I",data,0x2c)
    strings=struct.unpack_from("<I",data,0x64)[0]
    if not (120<=shader_start<=tex_start<=material_start<=bone_start<=strings<len(data)):
        raise ValueError("C5 section boundary invalid")
    if shader_start+8*nshader!=tex_start or tex_start+28*ntex!=material_start or material_start+52*nmaterial!=bone_start:
        raise ValueError("C5 material table stride/count invalid")
    if textures and (len(textures)!=ntex or [int(x["index"]) for x in textures]!=list(range(ntex))):
        raise ValueError("original C75 reference inventory mismatch")
    for t in textures:
        position=int(t["original_name_absolute_offset"])
        raw=t["original_texture_name"].encode("ascii")+b"\0"
        if not (strings<=position<len(data) and data[position:position+len(raw)]==raw):
            raise ValueError("original C75 texture name pointer mismatch")
    shaders=[]
    for i in range(nshader):
        first,relative=struct.unpack_from("<2I",data,shader_start+8*i)
        if first:raise ValueError("unsupported C5 shader header word")
        shader=name_at(data,strings+relative,len(data))
        if ";;;CF_" not in shader:raise ValueError("original shader capability pointer invalid")
        shaders.append(shader)
    rows=[]
    for i in range(nmaterial):
        words=struct.unpack_from("<13I",data,material_start+i*52)
        shader=words[0]&65535
        if shader>=nshader:raise ValueError("material shader reference out of bounds")
        material=name_at(data,strings+(words[8]&65535),len(data))
        slots=(words[1]&65535,words[1]>>16)
        if any(t!=65535 and t>=ntex for t in slots):
            raise ValueError("material texture reference out of bounds")
        names=[("" if t==65535 else (textures[t]["original_texture_name"] if textures else "UNKNOWN_SOURCE_ARCHIVE")) for t in slots]
        rows.append((i,material,shader,shaders[shader],*slots,*names,
            "VERIFIED_C5_C75" if textures or ntex==0 else "C5_ONLY_MISSING_C75",
            "UNVERIFIED"))
    return rows,{"nshader":nshader,"ntex":ntex,"nmaterial":nmaterial}

def scan(root,c75):
    textures=defaultdict(list)
    with c75.open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):textures[row["model_id"]].append(row)
    for records in textures.values():records.sort(key=lambda r:int(r["index"]))
    seen=set();models=[];rows=[];errors=[];kind=Counter()
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as z:
            for path in z.namelist():
                hit=C5_NAME.fullmatch(path)
                if not hit:continue
                model=hit.group(1)
                if model in seen:errors.append(model+": duplicate");continue
                seen.add(model)
                try:
                    values,metadata=parse(z.read(path),textures[model])
                except (ValueError,KeyError,UnicodeError,struct.error) as exc:
                    errors.append(f"{model}: {exc}")
                    continue
                models.append({"model_id":model,**metadata,
                               "verified_face_material_ranges":0})
                for value in values:
                    rows.append(dict(zip(FIELDS,(model,*value))))
                    a,b=value[4],value[5]
                    kind["no_texture" if a==b==65535 else
                         "texture_pair" if a!=65535 and b!=65535 else "single_or_special"]+=1
    if len(seen)!=730:errors.append(f"expected 730 models, found {len(seen)}")
    if set(textures)-seen:errors.append("unexpected original texture model")
    report={"model_count":len(seen),"material_references":len(rows),
            "shader_indices_validated":len(rows),
            "c75_texture_reference_slots":sum(
                x["source_reference_status"]=="VERIFIED_C5_C75" and
                x[f"texture_index{t}"]!=65535 for x in rows for t in (0,1)),
            "material_classes":dict(kind),
            "missing_c75_model_groups":sorted({x["model_id"] for x in rows if x["source_reference_status"]=="C5_ONLY_MISSING_C75"}),
            "verified_face_material_ranges":0,"errors":errors}
    return rows,models,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--texture-reference-csv",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    rows,models,report=scan(a.source_dir,a.texture_reference_csv)
    a.report.write_text(json.dumps({"report":report,"models":models},indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return int(bool(report["errors"]))
if __name__=="__main__":raise SystemExit(main())
