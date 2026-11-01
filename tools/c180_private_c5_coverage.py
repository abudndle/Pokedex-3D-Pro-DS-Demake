#!/usr/bin/env python3
"""Private C5 geometry coverage inventory; structural only, never asserts topology."""
import argparse, hashlib, json, struct, zipfile
from pathlib import Path
EXPECTED=set(range(734))-{721,722,723,724}
def inspect(data):
    if len(data)<0x78 or data[:2]!=b'\xc5\x78': raise ValueError("bad C5 header")
    u16=lambda p:struct.unpack_from('<H',data,p)[0]
    u32=lambda p:struct.unpack_from('<I',data,p)[0]
    a,b,c=[u32(p) for p in (0x3c,0x40,0x44)]
    n1,n2=u16(0x14),u16(0x16)
    if not(0x78<=a<=b<=c<=len(data)) or b-a!=n1*20 or c-b!=n2*12:
        raise ValueError("invalid descriptor table bounds")
    strides={}
    errors=[]
    for i in range(n1):
        off,res,packed,layout,res2=struct.unpack_from('<5I',data,a+i*20)
        count,stride=packed&65535,(packed>>16)&255
        strides[str(stride)]=strides.get(str(stride),0)+1
        if res or res2 or off+count*stride>len(data):
            errors.append("primary descriptor "+str(i))
    for i in range(n2):
        off,res,packed=struct.unpack_from('<3I',data,b+i*12)
        if res or off+(packed&65535)*(packed>>16)>len(data):
            errors.append("secondary descriptor "+str(i))
    return dict(sha256=hashlib.sha256(data).hexdigest(),primary=n1,secondary=n2,
                primary_strides=strides,structural_errors=errors,
                vertex_semantics_verified=False,topology_verified=False)
def audit(archives):
    records={}
    for path in archives:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.startswith("decoded_c5/p") or not name.endswith(".c5"):continue
                model=int(Path(name).stem[1:])
                if model not in EXPECTED or model in records:
                    raise ValueError("duplicate or out-of-roster model "+str(model))
                try: records[model]=inspect(z.read(name))
                except ValueError as exc: records[model]={"error":str(exc)}
    missing=sorted(EXPECTED-records.keys())
    failed=[model for model,row in records.items() if row.get("error") or row.get("structural_errors")]
    return dict(expected=len(EXPECTED),present=len(records),missing=missing,
                structural_failures=failed,all_structural_checks_passed=not missing and not failed,
                vertex_semantics_verified=False,topology_verified=False,
                models={f"p{k:03d}":records[k] for k in sorted(records)})
def main():
    p=argparse.ArgumentParser()
    p.add_argument("archives",nargs="+",type=Path)
    p.add_argument("--report",required=True,type=Path)
    args=p.parse_args()
    result=audit(args.archives)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n")
    print("C180",result["present"],"/",result["expected"],"structural failures",len(result["structural_failures"]))
    if not result["all_structural_checks_passed"]:raise SystemExit(1)
if __name__=="__main__":main()
