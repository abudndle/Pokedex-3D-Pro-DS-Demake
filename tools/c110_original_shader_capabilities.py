#!/usr/bin/env python3
"""Privately derive *declared shader capabilities* from original C5/C75.

P3SC is never proof of the original texture sampler/diffuse slot. Two distinct
C5 texture references remain ambiguous, even with CF_COLORMAP declared.
Keep original C5 and the produced P3SC sidecars OUT of the public repository.
"""
import argparse
import csv
import json
import re
import struct
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path

from c88_original_material_references import parse

NAME = re.compile(r"decoded_c5/(p\d{3})\.c5$")
ROSTER = {f"p{i:03d}" for i in range(734) if i not in (721, 722, 723, 724)}
CF_COLORMAP = 1
CF_BUMPMAP = 2
HEADER = "<4s4HI"
RECORD = "<5H"

def sidecar(model_id, raw, texture_rows):
    records, meta = parse(raw, texture_rows)
    if not 1 <= meta["nmaterial"] <= 256 or len(records) != meta["nmaterial"]:
        raise ValueError("unsupported original C5 material count")
    if meta["ntex"] and not texture_rows:
        raise ValueError("C75 original texture-name cross-check is mandatory")
    packed = bytearray()
    ambiguous = 0
    declared_colors = 0
    for i, material in enumerate(records):
        # C88 tuples: material index, name, source shader index/name,
        # source texture references, source texture names, source status.
        index, _, shader, shader_name, t0, t1 = material[:6]
        if index != i or not isinstance(shader_name, str) or ";;;CF_" not in shader_name:
            raise ValueError("invalid original C5 shader capability declaration")
        flags = shader_name.split(";;;", 1)[1].split(",")
        if not flags or any(re.fullmatch(r"CF_[A-Z0-9_]+", f) is None for f in flags):
            raise ValueError("malformed C5 shader flags")
        if len(flags) != len(set(flags)):
            raise ValueError("duplicate original C5 shader capabilities")
        mask = (CF_COLORMAP if "CF_COLORMAP" in flags else 0) | (
            CF_BUMPMAP if "CF_BUMPMAP" in flags else 0)
        declared_colors += bool(mask & CF_COLORMAP)
        ambiguous += bool(mask & CF_COLORMAP and t0 != 65535 and
                          t1 != 65535 and t0 != t1)
        packed += struct.pack(RECORD, index, shader, t0, t1, mask)
    header = struct.pack(HEADER, b"P3SC", 1, int(model_id[1:]), len(records),
                         0, zlib.crc32(packed))
    return header + packed, {"declared_colormap_materials": declared_colors,
                             "ambiguous_two_texture_colormap_materials": ambiguous,
                             "original_sampler_roles_verified": 0}

def build(root, c75_csv, output_zip, require_full=False):
    references = defaultdict(list)
    with Path(c75_csv).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = row.get("model_id", "")
            if re.fullmatch(r"p\d{3}", mid) is None:
                raise ValueError("invalid original C75 model ID")
            references[mid].append(row)
    for rows in references.values():
        rows.sort(key=lambda r: int(r["index"]))
    found = set()
    output = {}
    totals = {"models": 0, "declared_colormap_materials": 0,
              "ambiguous_two_texture_colormap_materials": 0,
              "original_sampler_roles_verified": 0,
              "requires_private_shader_sampler_decode": True}
    for part in (1, 2, 3):
        with zipfile.ZipFile(Path(root) /
                f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as z:
            if z.testzip() is not None:
                raise ValueError("corrupted original C5 archive")
            for filename in z.namelist():
                match = NAME.fullmatch(filename)
                if not match:
                    continue
                mid = match.group(1)
                if mid in found or mid not in ROSTER:
                    raise ValueError("duplicate or invalid original C5 model")
                found.add(mid)
                data, info = sidecar(mid, z.read(filename), references[mid])
                output[f"materials/{mid}.p3sc"] = data
                totals["models"] += 1
                for key in ("declared_colormap_materials",
                            "ambiguous_two_texture_colormap_materials"):
                    totals[key] += info[key]
    if set(references) - found:
        raise ValueError("original C75 references missing their C5 model")
    if require_full and found != ROSTER:
        raise ValueError("not all 730 original model shader declarations recovered")
    if not output:
        raise ValueError("no source-verified original shader declarations")
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(output):
            z.writestr(name, output[name])
    return totals

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-root", type=Path, required=True)
    p.add_argument("--texture-reference-csv", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--require-full", action="store_true")
    a = p.parse_args()
    try:
        result = build(a.private_root, a.texture_reference_csv, a.output, a.require_full)
    except (OSError, ValueError, KeyError, IndexError, struct.error,
            zipfile.BadZipFile) as exc:
        p.exit(1, f"C110 shader capability recovery rejected: {exc}\n")
    print(json.dumps(result, indent=2))
if __name__ == "__main__":
    main()
