#!/usr/bin/env python3
"""Validate private C99 Linux geometry QA screenshots without shipping game art.

Not an emulator screenshot validator. Evidence explicitly states the previews
are SOFTWARE_RENDERED and not screenshots of a running melonDS instance.
"""
import argparse
import json
import struct
import zlib
from pathlib import Path

PNG_MAGIC=b"\x89PNG\r\n\x1a\n"

def check_png(path):
    data=Path(path).read_bytes()
    if data[:8]!=PNG_MAGIC:raise ValueError("PNG signature invalid")
    at=8
    dimensions=None
    found_iend=False
    nontrivial=False
    raw_idat=bytearray()
    while at<len(data):
        if at+12>len(data):raise ValueError("PNG truncated chunk")
        n=struct.unpack_from(">I",data,at)[0]
        tag=data[at+4:at+8]
        end=at+12+n
        if end>len(data):raise ValueError("PNG chunk out of bounds")
        payload=data[at+8:at+8+n]
        crc=struct.unpack_from(">I",data,at+8+n)[0]
        if zlib.crc32(tag+payload)!=crc:raise ValueError("PNG CRC invalid")
        if tag==b"IHDR":
            if dimensions is not None or n!=13:raise ValueError("bad IHDR")
            width,height,bitdepth,colour,compression,filtering,interlace=struct.unpack(">IIBBBBB",payload)
            if bitdepth!=8 or colour!=2 or compression or filtering or interlace:
                raise ValueError("expected RGB888 noninterlaced PNG")
            dimensions=(width,height)
        elif tag==b"IDAT":
            raw_idat.extend(payload)
        elif tag==b"IEND":
            found_iend=True
            if end!=len(data):raise ValueError("extra bytes after IEND")
        at=end
    if not found_iend or dimensions!=(256,192):raise ValueError("not a DS-resolution PNG")
    pixels=zlib.decompress(raw_idat)
    if len(pixels)!=(1+256*3)*192:raise ValueError("PNG image payload size invalid")
    # Validate scanline filter markers; do not count compressed bytes as pixels.
    if any(pixels[row*(1+256*3)]>4 for row in range(192)):
        raise ValueError("invalid PNG row filter")
    if len(set(pixels))<4:raise ValueError("mostly uniform diagnostic screenshot")
    return {"width":256,"height":192,"png_crc_valid":True}

def verify(folder):
    folder=Path(folder)
    report=json.loads((folder/"C99_LINUX_RENDER_QA_REPORT.json").read_text())
    if report.get("platform")!="Linux (Pillow software rasterizer)" or report.get("tested_emulator")!="NONE" or report.get("melonds_test_passed") is not False or report.get("native_arm_rom_compiled_here") is not False or report.get("original_3ds_shader_parity_proven") is not False:
        raise ValueError("unverified emulator, ROM compilation or GPU parity claim")
    models=report.get("model_screenshots")
    if not isinstance(models,list) or not models:raise ValueError("missing source review records")
    seen=set()
    for row in models:
        model=row["model_id"]
        if model in seen:raise ValueError("duplicate model")
        seen.add(model)
        legacy=row["legacy_source_faces"]
        high=row["chunk_source_faces"]
        if not 0<legacy<=600 or not legacy<high<=1800:
            raise ValueError("invalid source face counts")
        if not 0<row["changed_pixels"]<=256*192:
            raise ValueError("unchanged original-source preview")
        images=row.get("software_images")
        # Each reported model must have the two exact, distinct geometry QA
        # views, not repeats of one image or a misleading emulator capture.
        required=[f"C99_SOFTWARE_QA_{model}_ds3m.png",
                  f"C99_SOFTWARE_QA_{model}_p3cs.png"]
        if (not isinstance(model,str) or
            not __import__("re").fullmatch(r"p[0-9]{3}",model) or
            not isinstance(images,list) or images!=required):
            raise ValueError("missing or mismatched source QA views")
        for name in images:
            if Path(name).name!=name or not name.endswith(".png"):
                raise ValueError("unsafe source screenshot path")
            check_png(folder/name)
    return {"models":len(seen),"software_screenshots":2*len(seen),
            "melonds_captures":0,"model_images_verified":True,
            "original_3ds_visual_fidelity_proven":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_evidence_dir",type=Path)
    args=p.parse_args()
    print(json.dumps(verify(args.private_evidence_dir),indent=2))
if __name__=="__main__":main()
