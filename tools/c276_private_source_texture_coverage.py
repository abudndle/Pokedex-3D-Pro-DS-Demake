#!/usr/bin/env python3
"""C276: verify C73 texture-byte SHA claims against private original C5.

Checks source payload hashes and texture index coverage only. Does NOT prove
P3PX RGB555 conversion, original GPU sampler roles, or DS textured rendering.
No private archive, source names, texture bytes, hashes or report in public CI.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

from c275_private_draw_material_chain import (MAX_MODEL, MAX_TOTAL, MAX_ENTRIES,
                                               ROSTER, c75_from_source,
                                               write_private_report)

MEMBER = re.compile(r"decoded_c5/(p\d{3})\.c5\Z")
HEX = re.compile(r"[a-fA-F0-9]{64}\Z")
MAX_C73_CSV = 4 * 1024 * 1024


def read_catalog(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_C73_CSV:
        raise ValueError("C73 texture catalog absent or over budget")
    rows = collections.defaultdict(dict)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        needed = {"model_id", "index", "source_offset", "source_bytes", "sha256", "provenance"}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError("C73 texture catalog missing columns")
        for row in reader:
            mid = row["model_id"]
            if mid not in ROSTER:
                raise ValueError("unexpected C73 model ID")
            try:
                idx, start, size = (int(row[key]) for key in ("index", "source_offset", "source_bytes"))
            except (ValueError, TypeError) as exc:
                raise ValueError("invalid C73 numeric field") from exc
            if (not 0 <= idx < 256 or start < 0 or not 0 < size <= MAX_MODEL
                    or not HEX.fullmatch(row["sha256"] or "")
                    or row["provenance"] != "C5_byte_exact"):
                raise ValueError("invalid C73 source byte provenance")
            if idx in rows[mid]:
                raise ValueError("duplicate C73 texture index")
            rows[mid][idx] = (start, size, row["sha256"].lower())
    return rows


def verify_model(model_id, source_c5, indexed):
    """Reject wrong source ranges/hashes and non-prefix catalog holes."""
    source_names = c75_from_source(source_c5)
    n = len(source_names)
    if not indexed:
        return {"model_id": model_id, "source_texture_count": n,
                "source_hash_verified": 0, "missing_source_texture_indices": n}
    if set(indexed) != set(range(len(indexed))) or len(indexed) > n:
        raise ValueError("C73 catalog indices are not a valid source prefix")
    for idx, (offset, size, digest) in indexed.items():
        if offset >= len(source_c5) or size > len(source_c5) - offset:
            raise ValueError("C73 original source texture bytes outside C5")
        if hashlib.sha256(source_c5[offset:offset + size]).hexdigest() != digest:
            raise ValueError("C73 original C5 source texture SHA-256 mismatch")
    return {"model_id": model_id, "source_texture_count": n,
            "source_hash_verified": len(indexed),
            "missing_source_texture_indices": n - len(indexed)}


def audit(private_root, c73_csv, require_full=False):
    catalog = read_catalog(c73_csv)
    seen = set()
    records = []
    consumed = 0
    for part in (1, 2, 3):
        with zipfile.ZipFile(Path(private_root) /
                f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as archive:
            if len(archive.infolist()) > MAX_ENTRIES:
                raise ValueError("original C5 ZIP entry budget exceeded")
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                    raise ValueError("symlinked original C5 member")
                match = MEMBER.fullmatch(info.filename)
                if not match:
                    if info.filename.lower().endswith(".c5"):
                        raise ValueError("unexpected original C5 member")
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in seen:
                    raise ValueError("duplicate or invalid original C5 model")
                seen.add(mid)
                if not 0 < info.file_size <= MAX_MODEL or consumed + info.file_size > MAX_TOTAL:
                    raise ValueError("original C5 byte budget exceeded")
                consumed += info.file_size
                raw = archive.read(info)
                records.append(verify_model(mid, raw, catalog.get(mid, {})))
    if not seen or set(catalog) - seen:
        raise ValueError("C73 catalog model missing original C5")
    if require_full and seen != ROSTER:
        raise ValueError("expected all 730 original C5 models")
    summary = {"schema": "C276_PRIVATE_SOURCE_TEXTURE_SHA_COVERAGE_V1",
               "original_models": len(seen),
               "source_c5_texture_pointers": sum(r["source_texture_count"] for r in records),
               "source_c5_texture_bytes_sha_verified": sum(r["source_hash_verified"] for r in records),
               "source_texture_indices_missing_from_c73": sum(r["missing_source_texture_indices"] for r in records),
               "models_missing_c73_catalog": sum(r["source_hash_verified"] == 0 for r in records),
               "verified_gpu_sampler_roles": 0,
               "verified_p3px_image_bytes": 0,
               "release_ready": False}
    return {"summary": summary, "models": sorted(records, key=lambda r: r["model_id"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--c73-csv", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(args.private_root, args.c73_csv, args.require_full)
        write_private_report(args.output_private_json, result)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            zipfile.BadZipFile) as exc:
        parser.exit(1, "C276 private source texture coverage rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
