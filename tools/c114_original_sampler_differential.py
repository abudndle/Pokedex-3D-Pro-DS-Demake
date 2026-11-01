#!/usr/bin/env python3
"""Compare verified original C5 material-operation words by shader/layout.

This is forensic DIFFERENTIAL evidence, not a decoded 3DS GPU sampler map.
Run on the private C111 evidence ZIP; do not publish source words or names.
"""
import argparse
import hashlib
import json
import math
import re
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

MODEL = re.compile(r"evidence/(p\d{3})\.json$")
HEX_WORD = re.compile(r"0x[0-9a-fA-F]{8}$")
SHA256 = re.compile(r"[0-9a-fA-F]{64}$")
MAX_RECORDS = 256

def validate_model(mid, model):
    if (model.get("schema")!="C111_ORIGINAL_C5_MATERIAL_WORDS_V1" or
        model.get("model_id")!=mid or
        not SHA256.fullmatch(str(model.get("source_C5_sha256",""))) or
        model.get("original_GPU_sampler_roles_verified")!=0):
        raise ValueError("C111 source provenance metadata missing/incorrect")
    rows=model.get("evidence")
    if not isinstance(rows,list) or not 1<=len(rows)<=MAX_RECORDS or model.get("material_count")!=len(rows):
        raise ValueError("invalid original C5 material record count")
    for i,row in enumerate(rows):
        textwords=row.get("source_material_words_hex")
        if (row.get("material_index")!=i or
            not isinstance(textwords,list) or len(textwords)!=13 or
            any(not isinstance(x,str) or HEX_WORD.fullmatch(x) is None for x in textwords) or
            not SHA256.fullmatch(str(row.get("source_material_record_sha256","")))):
            raise ValueError("invalid original C5 material word data")
        words=[int(x,16) for x in textwords]
        actual=hashlib.sha256(struct.pack("<13I",*words)).hexdigest()
        if actual!=row["source_material_record_sha256"].lower():
            raise ValueError("original C5 material word SHA-256 disagrees")
        refs=row.get("source_texture_references")
        if (not isinstance(refs,list) or len(refs)!=2 or
            not all(type(v) is int and 0<=v<=65535 for v in refs) or
            (words[0]&65535)!=row.get("shader_index") or
            [(words[1]&65535),words[1]>>16]!=refs or
            not isinstance(row.get("shader_declaration"),str)):
            raise ValueError("original C5 shader/texture references disagree")
    return rows

def texture_layout(refs):
    a,b=refs
    if a==b==65535:return "none"
    if a==65535:return "only_slot_1"
    if b==65535:return "only_slot_0"
    if a==b:return "two_slots_same_texture"
    return "two_distinct_slots"

def differential_report(source_zip,require_full=False):
    patterns=defaultdict(list)
    models=set()
    count=0
    with zipfile.ZipFile(source_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("corrupted C111 original evidence ZIP")
        for name in archive.namelist():
            hit=MODEL.fullmatch(name)
            if not hit:continue
            mid=hit.group(1)
            if mid in models:
                raise ValueError("duplicate original source model")
            models.add(mid)
            item=json.loads(archive.read(name))
            for row in validate_model(mid,item):
                words=[int(w,16) for w in row["source_material_words_hex"]]
                decl=row["shader_declaration"]
                layout=texture_layout(row["source_texture_references"])
                patterns[decl].append((mid,row["material_index"],layout,words))
                count+=1
    if not models:
        raise ValueError("no private C111 source material evidence")
    if require_full and len(models)!=730:
        raise ValueError("expected 730 recovered original C5 model groups")
    shader_groups=[]
    for declaration,items in sorted(patterns.items()):
        layout_counts={layout:sum(x[2]==layout for x in items)
                       for layout in sorted({x[2] for x in items})}
        # dword #0 stores shader ref; #1 is the two source texture indices;
        # #8 embeds a source-name pointer. These are known structural fields,
        # not decoded GPU sampler operation registers.
        unknown=(2,3,4,5,6,7,9,10,11,12)
        variation=[i for i in unknown if len({x[3][i] for x in items})>1]
        correlated=[]
        if len(layout_counts)>1:
            for i in unknown:
                by_layout={layout:{x[3][i] for x in items if x[2]==layout}
                           for layout in layout_counts}
                if len(set(frozenset(v) for v in by_layout.values()))>1:
                    correlated.append(i)
        shader_groups.append({
            "shader_declaration_sha256":hashlib.sha256(declaration.encode("utf-8")).hexdigest(),
            "original_material_count":len(items),
            "source_texture_reference_layouts":layout_counts,
            "unknown_material_word_offsets_with_variation":variation,
            "unknown_word_offsets_differing_by_reference_layout":correlated,
            "role_interpretation":"UNDECODED_GPU_OPERATIONS",
            "verified_color_sampler_assignments":0,
            "verified_normal_sampler_assignments":0,
        })
    return {
        "schema":"C114_ORIGINAL_SHADER_DIFFERENTIAL_V1",
        "source_model_count":len(models),
        "original_material_count":count,
        "original_shader_declaration_groups":len(shader_groups),
        "groups":shader_groups,
        "original_GPU_sampler_roles_decoded":0,
        "source_shader_instruction_disassembly_required":True,
        "release_ready":False
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-c111-evidence-zip",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--require-full",action="store_true")
    args=parser.parse_args()
    try:
        result=differential_report(args.private_c111_evidence_zip,args.require_full)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n")
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error,
            zipfile.BadZipFile,json.JSONDecodeError) as exc:
        parser.exit(1,"C114 source sampler differential rejected: "+str(exc)+"\n")
    print(json.dumps({"models":result["source_model_count"],
                      "materials":result["original_material_count"],
                      "shader_groups":result["original_shader_declaration_groups"],
                      "GPU_sampler_roles_decoded":0}))
if __name__=="__main__":
    main()
