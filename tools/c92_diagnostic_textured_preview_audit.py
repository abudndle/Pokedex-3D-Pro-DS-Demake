#!/usr/bin/env python3
"""Validate opt-in original-derived diagnostic textures. Never release them.

A P3MT created from source color *name hints* is not a proven original GPU
sampler binding. ZIP prefix enforces deliberate extraction before use.
"""
import argparse
import json
import re
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = "diagnostic_nitrofs/"
ENTRY = re.compile(r"diagnostic_nitrofs/(preview|materials|textures)/(p\d{3})(?:/(t\d{3}\.p3px)|\.(ds3m|p3uv|p3mt|p3tx))$")
VRAM = 128 * 1024

def le16(buf, at):
    return struct.unpack_from("<H", buf, at)[0]

def examine(path, require_full=False):
    rows = defaultdict(dict)
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError("duplicate or corrupted ZIP member")
        if "README_EXPERIMENTAL_PRIVATE_C92.txt" not in names:
            raise ValueError("missing private diagnostic-only disclaimer")
        for name in names:
            m = ENTRY.fullmatch(name)
            if m is None:
                if name != "README_EXPERIMENTAL_PRIVATE_C92.txt":
                    raise ValueError("unsafe or unexpected ZIP path")
                continue
            kind, model, subpath, extension = m.groups()
            role = extension if subpath is None else subpath
            if role in rows[model]:
                raise ValueError("duplicate model source resource")
            rows[model][role] = z.read(name)
    total_textures = total_ranges = total_faces = 0
    for model, files in rows.items():
        required = ("ds3m", "p3uv", "p3mt", "p3tx")
        if not all(x in files for x in required):
            raise ValueError(model + ": incomplete paired geometry, UV, material or manifest")
        ds, uv, mt, tx = (files[x] for x in required)
        if len(ds) < 16 or ds[:4] != b"DS3M" or le16(ds,4) != 2:
            raise ValueError(model + ": DS3M header invalid")
        triangles = le16(ds,6)
        if not 1 <= triangles <= 600 or len(ds) != 16 + 21*triangles:
            raise ValueError(model + ": DS3M size invalid")
        if len(uv) != 8+12*triangles or uv[:4] != b"P3UV" or le16(uv,4) != 1 or le16(uv,6) != triangles:
            raise ValueError(model + ": P3UV geometry does not match")
        if len(mt) < 8 or mt[:4] != b"P3MT" or le16(mt,4) != 1:
            raise ValueError(model + ": P3MT header invalid")
        n = le16(mt,6)
        if not 1 <= n <= 64 or len(mt) != 8 + 8*n:
            raise ValueError(model + ": P3MT range count invalid")
        if len(tx) < 8 or tx[:4] != b"P3TX" or le16(tx,4) != 1:
            raise ValueError(model + ": P3TX header invalid")
        nt = le16(tx,6)
        if not 1 <= nt <= 8 or len(tx) != 8 + nt*8:
            raise ValueError(model + ": texture manifest cap invalid")
        textures = {}
        bytes_used = 0
        previous = -1
        for j in range(nt):
            tid,w,h,fmt = struct.unpack_from("<4H",tx,8+j*8)
            if tid <= previous or fmt != 1 or any(
                s<8 or s>256 or s & (s-1) for s in (w,h)
            ):
                raise ValueError(model + ": invalid texture entry")
            previous = tid
            raw = files.get("t%03d.p3px" % tid)
            if raw is None or len(raw) != 10+2*w*h or raw[:4] != b"P3PX" or struct.unpack_from("<3H",raw,4)!=(2,w,h):
                raise ValueError(model + ": missing or mismatched original-derived P3PX")
            textures[tid] = True
            bytes_used += 2*w*h
        if bytes_used > VRAM:
            raise ValueError(model + ": over 128 KiB preview texture budget")
        if sum(x.endswith(".p3px") for x in files) != len(textures):
            raise ValueError(model + ": unreferenced diagnostic texture")
        cursor = 0
        for j in range(n):
            first,count,mat,tid = struct.unpack_from("<4H",mt,8+8*j)
            if first != cursor or not count or count > triangles-cursor or tid not in textures:
                raise ValueError(model + ": unverified or incomplete material range")
            cursor += count
        if cursor != triangles:
            raise ValueError(model + ": incomplete face coverage")
        total_ranges += n
        total_textures += nt
        total_faces += triangles
    if require_full and (len(rows),total_textures,total_ranges,total_faces)!=(500,1152,2147,299997):
        raise ValueError("C92 full 500-model diagnostic source batch incomplete")
    return {"diagnostic_models":len(rows),"original_derived_color_images":total_textures,
            "sampled_triangles":total_faces,"material_ranges":total_ranges,
            "original_GPU_sampler_roles_verified":0,
            "final_release_bindings_approved":0,
            "release_ready":False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("--require-c92-full-batch", action="store_true")
    a = p.parse_args()
    try:
        print(json.dumps(examine(a.archive,a.require_c92_full_batch),indent=2))
    except (OSError,ValueError,struct.error,zipfile.BadZipFile) as error:
        p.exit(1,"C92 diagnostic preview rejected: %s\n"%error)
if __name__ == "__main__":
    main()
