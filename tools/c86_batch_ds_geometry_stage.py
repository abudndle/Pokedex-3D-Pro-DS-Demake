#!/usr/bin/env python3
"""C86 private original-derived model geometry staging.

Public-safe source, private input ZIPs. Stage validated C18 source-derived
DS3M previews for every available model. Export 4.12-UV candidate DS3M/P3UV
pairs only when EVERY sampled source triangle has an original-extracted vt.
No invented mesh-to-material map, and no claim of exact 3DS visual parity.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import re
import struct
import zipfile
from pathlib import Path

MODELS = tuple(i for i in range(734) if i not in (721, 722, 723, 724))
MAX_TRI = 600
C18_PREFIX = "Pokedex3D_C18_BlocksDS/nitrofs/"
NEUTRAL = bytes((192, 224, 232))
OBJ_NAME = re.compile(r"(?:C62/|models/)p(\d{3})\.obj$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_preview(data: bytes) -> dict:
    if len(data) < 16:
        raise ValueError("truncated DS3M")
    magic, version, n, source_vertices, source_faces = struct.unpack_from("<4sHHII", data)
    if magic != b"DS3M" or version not in (1, 2) or not 1 <= n <= MAX_TRI:
        raise ValueError("invalid DS3M header")
    expected = 16 + n * (18 + (3 if version == 2 else 0))
    if len(data) != expected or source_vertices == 0 or source_faces < n:
        raise ValueError("invalid DS3M counts or length")
    coords = struct.unpack_from("<" + "h" * (n * 9), data, 16)
    if max(map(abs, coords)) >= 32767:
        raise ValueError("DS geometry fixed-point overflow")
    return {"triangle_count": n, "source_vertices": source_vertices,
            "source_faces": source_faces, "version": version}


def parse_uv_obj(raw: bytes):
    verts: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    groups: list[list[tuple[tuple[int, int, int], tuple[int, int, int]]]] = []
    current = None
    for line in io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="strict"):
        if line.startswith("v "):
            xyz = tuple(map(float, line.split()[1:4]))
            if len(xyz) != 3 or not all(map(math.isfinite, xyz)):
                raise ValueError("invalid xyz")
            verts.append(xyz)
        elif line.startswith("vt "):
            uv = tuple(map(float, line.split()[1:3]))
            if len(uv) != 2 or not all(map(math.isfinite, uv)):
                raise ValueError("invalid UV")
            uvs.append(uv)
        elif line.startswith(("o ", "g ")):
            current = []
            groups.append(current)
        elif line.startswith("f "):
            if current is None:
                current = []
                groups.append(current)
            p = line.split()[1:]
            if len(p) != 3:
                raise ValueError("nontriangular source face")
            vids, tids = [], []
            for part in p:
                fields = part.split("/")
                if not fields[0] or len(fields) < 2 or not fields[1]:
                    raise ValueError("UV missing from source face")
                v, t = int(fields[0]), int(fields[1])
                if not (1 <= v <= len(verts) and 1 <= t <= len(uvs)):
                    raise ValueError("bad vertex or UV index")
                vids.append(v - 1)
                tids.append(t - 1)
            current.append((tuple(vids), tuple(tids)))
    groups = [g for g in groups if g]
    if not verts or not uvs or not groups:
        raise ValueError("no source triangle or UV data")
    return verts, uvs, groups


def quotas(groups, limit=MAX_TRI):
    lengths = [len(g) for g in groups]
    if not lengths or len(lengths) > limit:
        raise ValueError("too many original mesh groups")
    remaining = min(sum(lengths), limit) - len(lengths)
    q = [1] * len(lengths)
    while remaining:
        candidates = [i for i, length in enumerate(lengths) if q[i] < length]
        if not candidates:
            break
        index = max(candidates, key=lambda i: (lengths[i] / q[i], -i))
        q[index] += 1
        remaining -= 1
    return q


def convert_complete_uv_obj(raw: bytes) -> tuple[bytes, bytes, dict]:
    verts, uvs, groups = parse_uv_obj(raw)
    lo = [min(x[a] for x in verts) for a in range(3)]
    hi = [max(x[a] for x in verts) for a in range(3)]
    max_extent = max(hi[a] - lo[a] for a in range(3))
    if not 0.00001 < max_extent < 100:
        raise ValueError("invalid source model dimensions")
    center = [(lo[a] + hi[a]) * .5 for a in range(3)]
    scale = 1.8 / max_extent
    coords = []
    uvpairs = []
    counts = quotas(groups)
    for group, take in zip(groups, counts):
        for k in range(take):
            face, tex = group[((2 * k + 1) * len(group)) // (2 * take)]
            p0, p1, p2 = (verts[i] for i in face)
            a = [p1[d] - p0[d] for d in range(3)]
            b = [p2[d] - p0[d] for d in range(3)]
            cr = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
            if sum(x*x for x in cr) < 1e-24:
                continue  # source degenerate triangle; no procedural replacements
            for i in face:
                for axis in range(3):
                    v = round((verts[i][axis] - center[axis]) * scale * 4096)
                    if not -32768 <= v <= 32766:
                        raise ValueError("source position cannot fit DS 4.12")
                    coords.append(v)
            for i in tex:
                for value in uvs[i]:
                    v = round(value * 4096)
                    if not -32768 <= v <= 32767:
                        raise ValueError("source UV cannot fit DS 4.12")
                    uvpairs.append(v)
    tri = len(coords) // 9
    if not 1 <= tri <= MAX_TRI or len(uvpairs) != tri * 6:
        raise ValueError("no valid paired geometry/UV triangles")
    source_faces = sum(map(len, groups))
    ds = struct.pack("<4sHHII", b"DS3M", 2, tri, len(verts), source_faces)
    ds += struct.pack("<" + "h"*len(coords), *coords)
    ds += NEUTRAL * tri
    puv = struct.pack("<4sHH", b"P3UV", 1, tri)
    puv += struct.pack("<" + "h"*len(uvpairs), *uvpairs)
    read_preview(ds)
    return ds, puv, {"original_vertices":len(verts), "original_faces":source_faces,
                     "source_mesh_groups":len(groups), "sampled_faces":tri}


def stage(base_c18: Path, uv_c62: Path, uv_c7: Path, output: Path, report: Path):
    status = []
    c18 = zipfile.ZipFile(base_c18)
    z62 = zipfile.ZipFile(uv_c62)
    z7 = zipfile.ZipFile(uv_c7)
    try:
        source_manifest = json.loads(c18.read(C18_PREFIX + "preview_manifest.json"))
        source_entries = {int(x["model"][1:]): x for x in source_manifest["models"]}
        if len(source_entries) != 726 or source_manifest.get("preview_models") != 726:
            raise ValueError("unrecognized original C18 preview inventory")
        candidate_count = 0
        color_cleaned = 0
        base_count = 0
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as dest:
            for id in MODELS:
                label = f"p{id:03d}"
                src = source_entries.get(id)
                if src is None:
                    status.append({"model_id":label,"fallback_preview":False,
                                   "paired_uv_candidate":False,"reason":"missing original C18 geometry"})
                    continue
                payload = c18.read(C18_PREFIX + f"preview/{label}.ds3m")
                if sha(payload) != src["preview_sha256"]:
                    raise ValueError(f"C18 source hash mismatch: {label}")
                head = read_preview(payload)
                if head["triangle_count"] != src["preview_triangles"] or head["source_faces"] != src["source_triangles"]:
                    raise ValueError(f"C18 source counts inconsistent: {label}")
                # C18 identified 14 samples with provisional guessed coloring.
                # In this private render package use neutral, rather than a
                # texture-zero guess erroneously presented as original colors.
                if src.get("provisional_texture_colored_triangles",0):
                    n = head["triangle_count"]
                    payload = payload[:16+n*18] + NEUTRAL*n
                    color_cleaned += 1
                dest.writestr(f"preview/{label}.ds3m", payload)
                base_count += 1
                uv_source = "none"
                name = f"C62/{label}.obj"
                if name in z62.namelist():
                    raw = z62.read(name)
                    uv_source = "C62 complete source-derived candidate"
                else:
                    name = f"models/{label}.obj"
                    if name in z7.namelist() and id not in (721,722,723,724):
                        raw = z7.read(name)
                        # C7 only had original-inferred vt for ten source files.
                        uv_source = "C7 earlier inferred UV candidate"
                    else:
                        raw = None
                paired = False
                detail = None
                reason = "no complete UV source export"
                if raw is not None:
                    try:
                        ds, uv, detail = convert_complete_uv_obj(raw)
                        dest.writestr(f"uv_candidates/{label}.ds3m",ds)
                        dest.writestr(f"uv_candidates/{label}.p3uv",uv)
                        paired = True
                        candidate_count += 1
                        reason = "candidate must be visually compared; material mapping unresolved"
                    except ValueError as exc:
                        reason = f"candidate conversion rejected: {exc}"
                status.append({"model_id":label,"fallback_preview":True,
                               "fallback_triangles":head["triangle_count"],
                               "paired_uv_candidate":paired,"source":uv_source,
                               "candidate_details":detail,"reason":reason})
            dest.writestr("README.txt",
                "C86 PRIVATE original-derived DS model preview package.\n"
                "preview/: 726 C18 source-derived fallback samples, 14 guessed-color models neutralized.\n"
                "uv_candidates/: separately staged matching DS3M/P3UV pairs from original C62/C7 OBJ exports.\n"
                "Candidate UVs are source-derived, but authentic texture/material associations unverified.\n"
                "Do not copy candidate P3UV alone onto unrelated existing DS3M geometry.\n"
                "Copy BOTH candidate .ds3m and .p3uv to preview/ for individual tests only.\n"
                "This is not an exact original 3DS model render nor a distributable release ROM.\n")
        result = {"source_model_records":len(MODELS), "source_derived_fallback_ds3m":base_count,
                  "neutralized_unverified_C18_colors":color_cleaned,
                  "complete_uv_paired_candidates":candidate_count,
                  "missing_c18_meshes":len(MODELS)-base_count,
                  "source_archive_sha256":{f.name:sha(f.read_bytes()) for f in (base_c18,uv_c62,uv_c7)},
                  "per_model":status}
        report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        return result
    finally:
        c18.close();z62.close();z7.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--c18",type=Path,required=True)
    p.add_argument("--c62",type=Path,required=True)
    p.add_argument("--c7",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    info=stage(args.c18,args.c62,args.c7,args.output,args.report)
    print(json.dumps({k:v for k,v in info.items() if k!="per_model"},indent=2))

if __name__=="__main__":main()