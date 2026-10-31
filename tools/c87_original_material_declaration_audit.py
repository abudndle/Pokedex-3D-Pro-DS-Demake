#!/usr/bin/env python3
"""Audit private original C5 shader strings and source texture-name pointers.

Metadata only. NEVER infer source mesh->material or material->texture links.
Only synthetic tests and code go in GitHub; private output stays local.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import re
import struct
import zipfile

C5 = re.compile(r"decoded_c5/(p\d{3})\.c5$")
SOURCE_FLAG = re.compile(rb"([\x20-\x7e]{2,64});;;((?:CF_[A-Z0-9_]+)(?:,CF_[A-Z0-9_]+)*)\x00")


def shader_declarations(data, first_texture_offset=None):
    if len(data)<0x78 or data[:2]!=b"\xc5x":
        raise ValueError("invalid C5 header")
    base=struct.unpack_from("<I",data,0x64)[0]
    if not 0x78<=base<len(data):
        raise ValueError("original C5 string table outside source")
    end=min(len(data),first_texture_offset if first_texture_offset is not None else base+131072)
    if end<=base or end-base>131072:
        raise ValueError("original string-table boundary invalid")
    result=[]
    for m in SOURCE_FLAG.finditer(data,base,end):
        flags=m.group(2).decode("ascii").split(",")
        if len(flags)!=len(set(flags)):
            raise ValueError("duplicate material capability")
        result.append((m.group(1).decode("ascii"),m.start(),flags))
    return result


def channel_hint(name):
    lower=name.lower()
    if "noros" in lower or "noreos" in lower:return "normal_candidate"
    if re.search(r"(?:cl[a-z]?_ctr|cl$)",lower):return "color_candidate"
    if re.search(r"(?:sp_ctr|_spec|_sp$)",lower):return "specular_candidate"
    if re.search(r"(?:env(?:\d+)?(?:_ctr)?$|_env\d+)",lower):return "environment_candidate"
    if lower.startswith("ef") or "_fire" in lower or "_dust" in lower:return "effect_candidate"
    return "unknown_channel"


def collect(source_dir, source_names_csv):
    original=collections.defaultdict(list)
    with source_names_csv.open(newline="",encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            original[row["model_id"]].append(row)
    found=set()
    flags=collections.Counter()
    labels=collections.Counter()
    channels=collections.Counter()
    records=[]
    errors=[]
    for i in (1,2,3):
        src=source_dir/f"Pokedex3D_C56_Decoded_C5_Part_{i}_of_3.zip"
        with zipfile.ZipFile(src) as z:
            for name in z.namelist():
                match=C5.fullmatch(name)
                if not match:continue
                mid=match.group(1)
                if mid in found:
                    errors.append(mid+": duplicate C5 source")
                    continue
                found.add(mid)
                data=z.read(name)
                textures=sorted(original[mid],key=lambda x:int(x["index"]))
                first=min((int(t["original_raw_source_offset"]) for t in textures),default=None)
                try:
                    shaders=shader_declarations(data,first)
                    for row in textures:
                        at=int(row["original_name_absolute_offset"])
                        name_bytes=row["original_texture_name"].encode("ascii")+b"\0"
                        if data[at:at+len(name_bytes)]!=name_bytes:
                            raise ValueError("C75 original string pointer mismatch")
                except (ValueError,KeyError,UnicodeError) as exc:
                    errors.append(f"{mid}: {exc}")
                    shaders=[]
                for label,_,cflags in shaders:
                    labels[label]+=1
                    flags.update(cflags)
                for row in textures:channels[channel_hint(row["original_texture_name"])]+=1
                if not shaders:errors.append(mid+": no recovered shader declarations")
                records.append({"model_id":mid,"declaration_count":len(shaders),
                    "source_texture_names":len(textures),
                    "capabilities":sorted({flag for _,_,f in shaders for flag in f}),
                    "verified_mesh_material_bindings":0})
    if len(found)!=730:errors.append("expected 730 original C5 model containers")
    if set(original)-found:errors.append("unknown original texture model")
    if sum(channels.values())!=4039:errors.append("expected 4039 original C75 texture names")
    report={"source_model_count":len(found),
       "shader_declarations":sum(labels.values()),
       "models_with_declarations":sum(r["declaration_count"]>0 for r in records),
       "source_texture_names_cross_checked":sum(channels.values()),
       "shader_labels":dict(labels),
       "shader_capability_counts":dict(flags),
       "texture_name_channel_hints":dict(channels),
       "verified_original_mesh_shader_links":0,
       "verified_original_mesh_texture_links":0,
       "errors":errors,
       "limitation":"Proves shader strings and texture-name pointers only; material/mesh/texture sampler links remain unverified."}
    return report,sorted(records,key=lambda r:r["model_id"])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-dir",type=Path,required=True)
    ap.add_argument("--texture-names-csv",type=Path,required=True)
    ap.add_argument("--output-report",type=Path,required=True)
    args=ap.parse_args()
    report,models=collect(args.source_dir,args.texture_names_csv)
    args.output_report.write_text(json.dumps({"report":report,"models":models},indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return bool(report["errors"])

if __name__=="__main__":
    raise SystemExit(main())
