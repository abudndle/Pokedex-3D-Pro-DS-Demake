#!/usr/bin/env python3
"""Recover byte-identical Nintendo 3DS audio containers from a PRIVATE CCI.

Header validation does not prove sound playback or full original sound routing.
No original audio data is included in this public repository.
"""
import argparse
import hashlib
import json
import mmap
import struct
import zipfile
from collections import Counter
from pathlib import Path

KINDS={
    b"CWAV":(0x7000,0x7001),
    b"CSTM":(0x4000,0x4001,0x4002),
    b"CSAR":(0x2000,0x2001,0x2002),
    b"CWAR":(0x6800,0x6801),
}

def validate_header(data,at,kind):
    if kind not in KINDS or at<0 or at+64>len(data):
        return None
    if data[at:at+4]!=kind or data[at+4:at+6]!=b"\xff\xfe":
        return None
    header,version,size,count=struct.unpack_from("<HIIH",data,at+6)
    if header!=64 or not 64<size<=64*1024*1024 or at+size>len(data):
        return None
    if count!=len(KINDS[kind]):return None
    sections=[];found=set()
    for i in range(count):
        t,reserved,start,length=struct.unpack_from("<HHII",data,at+20+i*12)
        if t not in KINDS[kind] or t in found or reserved or start<header or length<4 or start+length>size:
            return None
        found.add(t);sections.append((start,length))
    if found!=set(KINDS[kind]):return None
    sorted_sections=sorted(sections)
    if any(a[0]+a[1]>b[0] for a,b in zip(sorted_sections,sorted_sections[1:])):
        return None
    return {"size":size,"version":f"0x{version:08x}","section_count":count}

def recover(private_cci,private_zip,private_report):
    paths=[Path(private_cci).resolve(),Path(private_zip).resolve(),Path(private_report).resolve()]
    if len(set(paths))!=3:raise ValueError("private output would overwrite an input")
    records=[];unique={}
    with open(private_cci,"rb") as fh,mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ) as source:
        for kind in KINDS:
            at=0
            while True:
                offset=source.find(kind,at)
                if offset<0:break
                at=offset+4
                header=validate_header(source,offset,kind)
                if header is None:continue
                data=source[offset:offset+header["size"]]
                digest=hashlib.sha256(data).hexdigest()
                name="original_audio/"+kind.decode().lower()+f"/{len(records):06d}_{offset:08x}."+kind.decode().lower()
                records.append({"format":kind.decode(),"offset":offset,"size":len(data),
                    "sha256":digest,"section_count":header["section_count"],
                    "version":header["version"],"archive_path":name,
                    "duplicate_of_offset":unique.get(digest,"")})
                unique.setdefault(digest,offset)
        with zipfile.ZipFile(private_zip,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as z:
            for row in records:
                z.writestr(row["archive_path"],source[row["offset"]:row["offset"]+row["size"]])
            z.writestr("README_PRIVATE_SOURCE_ONLY.txt",
                "PRIVATE ORIGINAL 3DS AUDIO CONTAINERS. NOT A WORKING DS AUDIO PORT.\n"
                "Never distribute commercial audio data or commit it to public GitHub.\n")
    summary={"milestone":"C102","format_counts":dict(Counter(x["format"] for x in records)),
        "audio_containers":len(records),
        "total_source_container_bytes":sum(x["size"] for x in records),
        "unique_container_sha256":len(unique),
        "duplicate_content_entries":len(records)-len(unique),
        "Nintendo_DS_audio_playback_implemented":False,
        "original_3ds_sound_routing_verified":False,
        "private_audio_only":True,"records":records}
    Path(private_report).write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(private_zip) as z:
        if z.testzip() is not None or len(z.namelist())!=len(records)+1:
            raise ValueError("private source archive failed CRC/entry validation")
    return summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private-cci",required=True,type=Path)
    ap.add_argument("--private-audio-zip",required=True,type=Path)
    ap.add_argument("--private-report",required=True,type=Path)
    args=ap.parse_args()
    result=recover(args.private_cci,args.private_audio_zip,args.private_report)
    print(json.dumps({k:v for k,v in result.items() if k!="records"},indent=2))
if __name__=="__main__":main()
