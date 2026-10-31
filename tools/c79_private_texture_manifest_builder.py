#!/usr/bin/env python3
"""Build private P3TX manifests from verified per-model P3PX files.

No P3MT material bindings are inferred. The output contains only texture
IDs/dimensions/format, not commercial game pixels or source texture names.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path

PIXEL_PATH = re.compile(r"textures/(p\d{3})/t(\d{3})\.p3px$")
CATALOG_PATH = re.compile(r"catalogs/(p\d{3})\.p3tm$")
BUDGET = 128 * 1024


def p3tx_bytes(items):
    if len(items) > 64:
        raise ValueError("P3TX entry cap exceeded")
    output = bytearray(struct.pack("<4sHH", b"P3TX", 1, len(items)))
    previous = -1
    for ident, width, height in items:
        if ident <= previous or not 0 <= ident <= 65535:
            raise ValueError("texture IDs must be strictly ascending")
        if any(x < 8 or x > 256 or x & (x - 1) for x in (width, height)):
            raise ValueError("unsupported DS texture dimensions")
        output += struct.pack("<4H", ident, width, height, 1)
        previous = ident
    return bytes(output)


def scan(csv_file, pixel_zip, catalog_zip, destination=None):
    with csv_file.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("no texture records")
    counts = {}
    with zipfile.ZipFile(catalog_zip) as archive:
        for filename in archive.namelist():
            match = CATALOG_PATH.fullmatch(filename)
            if not match or match.group(1) in counts:
                raise ValueError("unknown or duplicate model catalog")
            raw = archive.read(filename)
            if len(raw) < 20 or raw[:4] != b"P3TM":
                raise ValueError("invalid original catalog header")
            version, ident, n, flags, length, checksum = struct.unpack_from("<4HII", raw, 4)
            if version != 1 or ident != int(match.group(1)[1:]) or flags or length != len(raw) - 20 or zlib.crc32(raw[20:]) != checksum:
                raise ValueError("invalid original catalog body")
            counts[match.group(1)] = n
    mapped = collections.defaultdict(list)
    with zipfile.ZipFile(pixel_zip) as archive:
        for row in rows:
            model = row["model_id"]
            filename = row["output_path"]
            match = PIXEL_PATH.fullmatch(filename)
            ident, width, height = int(row["index"]), int(row["ds_width"]), int(row["ds_height"])
            if model not in counts or match is None or match.group(1) != model or int(match.group(2)) != ident:
                raise ValueError("invalid model-local texture reference")
            pixel = archive.read(filename)
            if len(pixel) < 10 or pixel[:4] != b"P3PX" or struct.unpack_from("<HHH", pixel, 4) != (2, width, height):
                raise ValueError("unexpected texture header or format")
            if len(pixel) != 10 + 2 * width * height or hashlib.sha256(pixel).hexdigest() != row["p3px_sha256"]:
                raise ValueError("invalid texture size or SHA-256")
            mapped[model].append((ident, width, height))
    report = []
    outputs = []
    for model in sorted(counts):
        entries = sorted(mapped[model])
        if len(entries) != counts[model] or [e[0] for e in entries] != list(range(len(entries))):
            raise ValueError(f"{model}: texture inventory/catalog mismatch")
        if entries:
            outputs.append((f"materials/{model}.p3tx", p3tx_bytes(entries)))
        total = sum(2 * w * h for _, w, h in entries)
        report.append({"model_id": model, "texture_count": len(entries),
                       "all_texture_bytes": total,
                       "all_fit_128kb": total <= BUDGET,
                       "manifest_generated": bool(entries),
                       "mesh_material_binding": "NOT_VERIFIED"})
    if destination is not None:
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, data in outputs:
                archive.writestr(path, data)
            archive.writestr("README.txt",
                "Private texture metadata only. No original P3MT mesh-material map is inferred.\n"
                "Do not claim full DS rendering until original material references are verified.\n")
    summary = {"models": len(counts), "verified_p3px": len(rows),
               "model_manifest_count": len(outputs),
               "models_missing_source_textures": len(counts) - len(outputs),
               "models_over_128kb_if_all_textures_loaded":
                   sum(not item["all_fit_128kb"] for item in report),
               "verified_original_mesh_material_bindings": 0}
    return report, summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--textures-csv", type=Path, required=True)
    p.add_argument("--pixels-zip", type=Path, required=True)
    p.add_argument("--catalogs-zip", type=Path, required=True)
    p.add_argument("--output-zip", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    records, summary = scan(args.textures_csv, args.pixels_zip, args.catalogs_zip, args.output_zip)
    args.report.write_text(json.dumps({"summary": summary, "models": records}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
