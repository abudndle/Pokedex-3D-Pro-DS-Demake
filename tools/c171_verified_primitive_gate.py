"""C171: fail-closed gate for using original C5 primitives in native rendering.

A descriptor count or float signature cannot authorize source geometry.
Only an explicit independently verified primitive map may pass this gate.
"""
import argparse
import json
from pathlib import Path

SCHEMA="p3d-c171-verified-primitives-v1"

def verify(manifest):
    if not isinstance(manifest,dict) or manifest.get("schema")!=SCHEMA:
        raise ValueError("unsupported primitive evidence schema")
    if manifest.get("source")!="original-c5" or manifest.get("method")!="verified-original-primitive-order":
        raise ValueError("unverified source primitive mapping")
    if manifest.get("verified_by") not in ("source-decoder-crosscheck","reference-renderer-crosscheck"):
        raise ValueError("independent decoder/reference verification required")
    rows=manifest.get("meshes")
    if not isinstance(rows,list) or not rows:
        raise ValueError("no verified mesh mappings")
    seen=set()
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("invalid mesh mapping")
        model,mesh,triangles=row.get("model"),row.get("mesh"),row.get("triangles")
        if not isinstance(model,str) or len(model)!=4 or model[0]!="p" or not model[1:].isdigit() or not 0<=int(model[1:])<=733 or 721<=int(model[1:])<=724:
            raise ValueError("invalid original model identifier")
        if not isinstance(mesh,int) or isinstance(mesh,bool) or mesh<0:
            raise ValueError("invalid mesh identifier")
        if not isinstance(triangles,list) or not triangles:
            raise ValueError("missing original triangles")
        key=(model,mesh)
        if key in seen:raise ValueError("duplicate mesh mapping")
        seen.add(key)
        for tri in triangles:
            if not isinstance(tri,list) or len(tri)!=3 or any(not isinstance(i,int) or isinstance(i,bool) or i<0 for i in tri):
                raise ValueError("invalid triangle indices")
            if len(set(tri))!=3:raise ValueError("degenerate triangle")
    return {"verified_meshes":len(seen),"verified_triangles":sum(len(x["triangles"]) for x in rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("private_manifest",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(json.loads(a.private_manifest.read_text())),sort_keys=True))
if __name__=="__main__":main()
