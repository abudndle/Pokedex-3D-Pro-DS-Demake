"""C173: export verified original primitive maps as bounded, portable DS index streams.

This exporter never guesses original geometry. It accepts only a C171/C172
verified map plus the matching private original C5 model, and writes a compact
index stream for downstream native integration. Keep exports private.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from c172_primitive_coverage_gate import verify_coverage

MAGIC=b"P3IX"
VERSION=1

def export(manifest, source):
    verify_coverage(manifest,source)
    model=int(manifest["model"][1:])
    rows=sorted(manifest["meshes"],key=lambda r:r["mesh"])
    if len(rows)>65535:raise ValueError("too many meshes")
    output=bytearray(struct.pack("<4sHHH",MAGIC,VERSION,model,len(rows)))
    for row in rows:
        triangles=row["triangles"]
        if len(triangles)>0xffffffff//3:raise ValueError("too many triangles")
        output+=struct.pack("<HI",row["mesh"],len(triangles))
        for triangle in triangles:
            if any(i>65535 for i in triangle):
                raise ValueError("DS u16 vertex index limit exceeded")
            output+=struct.pack("<3H",*triangle)
    return bytes(output)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("private_manifest",type=Path)
    p.add_argument("private_c5_archive",type=Path)
    p.add_argument("private_output",type=Path)
    a=p.parse_args()
    manifest=json.loads(a.private_manifest.read_text())
    with zipfile.ZipFile(a.private_c5_archive) as z:
        source=z.read("decoded_c5/"+manifest["model"]+".c5")
    result=export(manifest,source)
    a.private_output.parent.mkdir(parents=True,exist_ok=True)
    a.private_output.write_bytes(result)
    print(json.dumps({"bytes":len(result),"model":manifest["model"],
                      "verified_meshes":len(manifest["meshes"])}))
if __name__=="__main__":main()
