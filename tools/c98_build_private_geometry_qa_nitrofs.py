#!/usr/bin/env python3
"""C98: private opt-in DS3M / P3CS comparison NitroFS packager.

Works only with the user's privately recovered original game assets. Nothing
original-derived is committed to public source control. The synthetic species
map is explicitly DIAGNOSTIC, NOT the original game's resource mapping.
"""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

DS3M=re.compile(r"preview/p(\d{3})\.ds3m$")
P3CS=re.compile(r"diagnostic_nitrofs/preview/p(\d{3})\.p3cs$")
DIAGNOSTIC_MODELS=(0,1,25)

def qa_species_map():
    mapping=[0xffff]*649
    for species,model in ((0,0),(1,1),(24,25)):
        mapping[species]=model
    return struct.pack("<4sHH",b"P3SM",1,649)+struct.pack("<649H",*mapping)

def inspect_sources(legacy_zip,chunk_zip,expected_legacy=726,expected_chunks=500):
    with zipfile.ZipFile(legacy_zip) as old,zipfile.ZipFile(chunk_zip) as chunks:
        old_names=old.namelist()
        chunk_names=chunks.namelist()
        if (len(old_names)!=len(set(old_names)) or len(chunk_names)!=len(set(chunk_names))
                or old.testzip() is not None or chunks.testzip() is not None):
            raise ValueError("duplicate or corrupted private source archive")
        legacy={int(DS3M.fullmatch(x).group(1)) for x in old_names if DS3M.fullmatch(x)}
        chunk={int(P3CS.fullmatch(x).group(1)) for x in chunk_names if P3CS.fullmatch(x)}
        if len(legacy)!=expected_legacy or len(chunk)!=expected_chunks:
            raise ValueError("incorrect original-derived source model inventory")
        if not set(DIAGNOSTIC_MODELS)<=legacy&chunk:
            raise ValueError("three paired diagnostic source models not present")
        for n in old_names:
            if n.startswith("/") or ".." in n.split("/"):
                raise ValueError("unsafe recovered asset path")
        return old_names,[x for x in chunk_names if P3CS.fullmatch(x)]

def build(legacy_zip,chunk_zip,out,expected_legacy=726,expected_chunks=500):
    old_names,selected=inspect_sources(legacy_zip,chunk_zip,expected_legacy,expected_chunks)
    out=Path(out)
    seen=set(old_names)
    for entry in selected:
        dest=entry.removeprefix("diagnostic_nitrofs/")
        if dest in seen:raise ValueError("original asset filename collision")
        seen.add(dest)
    if "models/species_map.p3sm" in seen:
        raise ValueError("cannot overwrite original game model/species map")
    with zipfile.ZipFile(legacy_zip) as old,zipfile.ZipFile(chunk_zip) as chunks:
        with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as target:
            for name in old_names:target.writestr(name,old.read(name))
            for source in selected:target.writestr(source.removeprefix("diagnostic_nitrofs/"),chunks.read(source))
            target.writestr("models/species_map.p3sm",qa_species_map())
    with zipfile.ZipFile(out) as result:
        if result.testzip() is not None or len(result.namelist())!=len(old_names)+len(selected)+1:
            raise ValueError("private QA pack integrity failure")
    return {"purpose":"PRIVATE_DIAGNOSTIC_ONLY","legacy_model_count":expected_legacy,
            "chunk_model_count":expected_chunks,"entries":len(old_names)+len(selected)+1,
            "test_species_map_only":True,"authentic_species_map":False,
            "verified_3ds_texture_sampler_roles":False,"release_ready":False,
            "archive_sha256":hashlib.sha256(out.read_bytes()).hexdigest()}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legacy-zip",type=Path,required=True)
    ap.add_argument("--chunk-zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    report=build(a.legacy_zip,a.chunk_zip,a.out)
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    main()
