#!/usr/bin/env python3
"""Inspect private NCSD/NCCH section boundaries. Never exports game payloads."""
import argparse
import json
import struct
from pathlib import Path
UNIT=512
def inventory(path):
    size=path.stat().st_size
    with path.open("rb") as f:
        table=f.read(UNIT)
        if len(table)!=UNIT or table[0x100:0x104]!=b"NCSD":raise ValueError("Not NCSD")
        result={"image_bytes":size,"partitions":[]}; occupied=[]
        for i in range(8):
            start,count=struct.unpack_from("<II",table,0x120+8*i)
            if not start and not count:continue
            lo,hi=start*UNIT,(start+count)*UNIT
            if not start or not count or lo<UNIT or hi>size or any(lo<b and a<hi for a,b in occupied):
                raise ValueError("Invalid NCSD partition %d"%i)
            occupied.append((lo,hi));f.seek(lo);h=f.read(UNIT)
            if h[0x100:0x104]!=b"NCCH":raise ValueError("Missing NCCH header")
            part={"index":i,"offset":lo,"size":hi-lo,"sections":{}}
            for name,position in (("plain",0x190),("logo",0x198),("exefs",0x1a0),("romfs",0x1b0)):
                off,n=struct.unpack_from("<II",h,position)
                if not off and not n:continue
                s,e=lo+off*UNIT,lo+(off+n)*UNIT
                if not off or not n or s<lo+UNIT or e>hi:raise ValueError("Invalid "+name)
                entry={"offset":s,"size":e-s}
                f.seek(s);prefix=f.read(min(UNIT,e-s))
                if name=="romfs":entry["ivfc_magic"]=prefix[:4]==b"IVFC"
                if name=="exefs":
                    files=[]
                    for j in range(10):
                        raw=prefix[j*16:j*16+8]
                        sub,sz=struct.unpack_from("<II",prefix,j*16+8)
                        if sub==0 and sz==0:continue
                        label=raw.split(b"\0",1)[0].decode("ascii","replace")
                        if not label or sub+sz>e-s-UNIT:raise ValueError("ExeFS file out of bounds")
                        files.append({"name":label,"offset":s+UNIT+sub,"size":sz})
                    entry["files"]=files
                part["sections"][name]=entry
            result["partitions"].append(part)
        return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("image",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args();s=json.dumps(inventory(a.image),indent=2)+"\n"
    if a.output:a.output.write_text(s,encoding="utf-8")
    else:print(s,end="")
