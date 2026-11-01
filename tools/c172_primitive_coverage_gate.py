"""C172: validate independently verified primitive maps against source C5 mesh counts.

A map must cover every triangle of each claimed mesh; partial maps cannot be
silently promoted to authentic native geometry. Original bytes stay private.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from c171_verified_primitive_gate import verify

def verify_coverage(manifest, source):
    summary=verify(manifest)
    vstart,istart=struct.unpack_from("<2I",source,0x3c)
    model=manifest.get("model")
    if not isinstance(model,str) or len(model)!=4 or model[0]!="p" or not model[1:].isdigit():
        raise ValueError("invalid model identity")
    if any(row["model"]!=model for row in manifest["meshes"]):
        raise ValueError("cross-model mapping")
    n=struct.unpack_from("<H",source,0x10)[0]
    for row in manifest["meshes"]:
        mesh=row["mesh"]
        if mesh>=n:raise ValueError("mesh index outside original model")
        vertex_count=struct.unpack_from("<I",source,vstart+20*mesh+8)[0]&65535
        packed=struct.unpack_from("<I",source,istart+12*mesh+8)[0]
        count=packed&65535
        if count%3 or len(row["triangles"])!=count//3:
            raise ValueError("incomplete original triangle coverage")
        if any(i>=vertex_count for tri in row["triangles"] for i in tri):
            raise ValueError("triangle references vertex outside source mesh")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("private_manifest",type=Path)
    p.add_argument("private_c5_archive",type=Path)
    a=p.parse_args()
    manifest=json.loads(a.private_manifest.read_text())
    with zipfile.ZipFile(a.private_c5_archive) as z:
        source=z.read("decoded_c5/"+manifest["model"]+".c5")
    print(json.dumps(verify_coverage(manifest,source),sort_keys=True))
if __name__=="__main__":main()
