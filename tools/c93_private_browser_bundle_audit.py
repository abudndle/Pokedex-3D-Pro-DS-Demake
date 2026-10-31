#!/usr/bin/env python3
"""Audit optional private C93 browser bundle integrity. No game assets bundled."""
import argparse
import base64
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

PATTERN=re.compile(r"const MODEL_PAYLOADS=(\\{.*?\\});\\nconst ids=",re.S)

def audit(html,provenance):
    raw=html.read_text(encoding="utf-8")
    match=PATTERN.search(raw)
    if match is None:raise ValueError("missing embedded model assets")
    payloads=json.loads(match.group(1))
    report=json.loads(provenance.read_text(encoding="utf-8"))
    if set(payloads)!=set(report["models"]) or len(payloads)!=report["model_count"]:
        raise ValueError("model roster does not match provenance")
    total_faces=total_textures=full=0
    for mid,encoded in payloads.items():
        expected=report["models"][mid]
        compressed=base64.b64decode(encoded,validate=True)
        if hashlib.sha256(compressed).hexdigest()!=expected["compressed_sha256"]:
            raise ValueError(mid+": compressed asset hash mismatch")
        original=zlib.decompress(compressed)
        if hashlib.sha256(original).hexdigest()!=expected["uncompressed_sha256"]:
            raise ValueError(mid+": original-derived asset hash mismatch")
        if len(original)<16:raise ValueError("source bundle truncated")
        dslen,uvlen,mtlen,texcount=struct.unpack_from("<4I",original)
        p=16
        ds=original[p:p+dslen];p+=dslen
        uv=original[p:p+uvlen];p+=uvlen
        mt=original[p:p+mtlen];p+=mtlen
        if ds[:4]!=b"DS3M" or uv[:4]!=b"P3UV" or mt[:4]!=b"P3MT":
            raise ValueError(mid+": invalid source geometry, UV or material header")
        n=struct.unpack_from("<H",ds,6)[0]
        if not 1<=n<=16000 or dslen!=16+n*21 or uvlen!=8+n*12 or struct.unpack_from("<H",uv,6)[0]!=n:
            raise ValueError(mid+": UV triangle count mismatch")
        for tag,blob in (("ds3m",ds),("p3uv",uv),("p3mt",mt)):
            if hashlib.sha256(blob).hexdigest()!=expected["source_file_sha256"][tag]:
                raise ValueError(mid+": altered source file "+tag)
        ranges=struct.unpack_from("<H",mt,6)[0]
        cursor=0
        for j in range(ranges):
            first,count,material,tid=struct.unpack_from("<4H",mt,8+j*8)
            if first!=cursor or not count:raise ValueError(mid+": source face range gap")
            cursor+=count
        if cursor!=n:raise ValueError(mid+": uncovered source faces")
        for j in range(texcount):
            if p+6>len(original):raise ValueError(mid+": missing texture header")
            tid,size=struct.unpack_from("<HI",original,p);p+=6
            pixels=original[p:p+size];p+=size
            if len(pixels)!=size or pixels[:4]!=b"P3PX":
                raise ValueError(mid+": damaged private pixel payload")
            name="t%03d.p3px"%tid
            if hashlib.sha256(pixels).hexdigest()!=expected["source_file_sha256"][name]:
                raise ValueError(mid+": original-derived texture SHA mismatch")
            version,width,height=struct.unpack_from("<3H",pixels,4)
            if version!=2 or size!=10+2*width*height:
                raise ValueError(mid+": malformed texture dimensions")
        if p!=len(original):raise ValueError(mid+": unexpected bytes in original bundle")
        full+=int(expected["geometry_mode"]=="FULL_ORIGINAL_OBJ_FOR_BROWSER_ONLY")
        total_faces+=n
        total_textures+=texcount
    if report.get("native_3ds_shader_equivalence_verified") is not False or report.get("original_sampler_channels_proven") is not False:
        raise ValueError("unsubstantiated 3DS GPU fidelity claim")
    return {"models":len(payloads),"full_original_obj_browser_references":full,
            "total_display_triangles":total_faces,"source_derived_images":total_textures,
            "original_shader_3ds_fidelity_proven":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html",type=Path,required=True)
    p.add_argument("--provenance",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(audit(a.html,a.provenance),indent=2))
if __name__=="__main__":main()
