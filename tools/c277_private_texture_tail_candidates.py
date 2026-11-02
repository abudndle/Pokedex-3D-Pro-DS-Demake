#!/usr/bin/env python3
"""C277: bounded, private original-C5 texture tail-layout *candidate* audit.

The C5 descriptor offsets/sizes can describe a contiguous end-of-file tail.
An EOF-derived base is a hypothesis, NOT an independently proven original
texture-payload pointer. Existing C73 source offsets/SHA rows can corroborate
it for their models; a model without C73 rows remains unverified. Never emit
original pixels, source hashes, offsets or texture names in public CI/logs.
"""
import argparse
import hashlib
import json
import stat
import struct
import zipfile
from pathlib import Path

from c275_private_draw_material_chain import (MAX_ENTRIES, MAX_MODEL, MAX_TOTAL,
                                               MEMBER, ROSTER, c75_from_source,
                                               write_private_report)
from c276_private_source_texture_coverage import read_catalog

SCHEMA = "C277_PRIVATE_C5_TEXTURE_TAIL_CANDIDATES_V1"


def candidates(raw):
    """Return candidate absolute source ranges from a strictly contiguous tail."""
    if not isinstance(raw, bytes) or not 120 <= len(raw) <= MAX_MODEL:
        raise ValueError("original C5 source size invalid")
    # This checks the original header, table ordering, and texture-name pointers.
    names = c75_from_source(raw)
    n = len(names)
    table = struct.unpack_from("<I", raw, 0x30)[0]
    strings_at = struct.unpack_from("<I", raw, 0x64)[0]
    expected = 0
    offsets = []
    for i in range(n):
        relative = struct.unpack_from("<I", raw, table + i * 28)[0]
        size = struct.unpack_from("<I", raw, table + i * 28 + 12)[0]
        if size == 0 or size > MAX_MODEL or relative != expected:
            raise ValueError("C5 texture descriptor tail not contiguous")
        expected += size
        if expected > MAX_MODEL:
            raise ValueError("C5 texture descriptor byte budget exceeded")
        offsets.append((relative, size))
    if not offsets or expected > len(raw):
        raise ValueError("C5 texture descriptor tail outside source")
    base = len(raw) - expected
    if base <= strings_at:
        raise ValueError("C5 texture candidate tail overlaps source string table")
    return [(base + offset, size, hashlib.sha256(raw[base + offset:base + offset + size]).hexdigest())
            for offset, size in offsets]


def verify_model(model_id, raw, indexed):
    """Cross-check C73 source offsets/sizes/SHA; never promote unanchored rows."""
    if model_id not in ROSTER:
        raise ValueError("invalid original C5 model roster")
    rows = candidates(raw)
    if set(indexed) != set(range(len(indexed))) or len(indexed) > len(rows):
        raise ValueError("C73 texture catalog indices are not a valid source prefix")
    for i, (offset, size, digest) in indexed.items():
        if (offset, size, digest) != rows[i]:
            raise ValueError("C73 source range/SHA disagrees with original C5 tail candidate")
    missing = [{"index": i, "candidate_source_offset": offset,
                "descriptor_source_bytes": size, "candidate_sha256": digest,
                "status": "UNVERIFIED_EOF_TAIL_HYPOTHESIS"}
               for i, (offset, size, digest) in enumerate(rows) if i not in indexed]
    return {"model_id": model_id, "source_texture_descriptors": len(rows),
            "c73_corrob_source_ranges": len(indexed),
            "c73_independent_model_anchor": bool(indexed),
            "candidate_missing_rows": missing,
            "verified_missing_source_payload_bases": 0}


def audit(private_root, c73_csv, require_full=False):
    catalog = read_catalog(c73_csv)
    seen = set()
    records = []
    consumed = 0
    for part in (1, 2, 3):
        path = Path(private_root) / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ENTRIES:
                raise ValueError("original C5 ZIP entry budget exceeded")
            for info in members:
                if info.is_dir():
                    continue
                if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                    raise ValueError("symlinked original C5 ZIP member")
                match = MEMBER.fullmatch(info.filename)
                if not match:
                    if info.filename.lower().endswith(".c5"):
                        raise ValueError("unexpected original C5 ZIP member")
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in seen:
                    raise ValueError("duplicate or invalid original C5 model")
                seen.add(mid)
                if not 0 < info.file_size <= MAX_MODEL or consumed + info.file_size > MAX_TOTAL:
                    raise ValueError("original C5 ZIP byte budget exceeded")
                consumed += info.file_size
                raw = archive.read(info)
                if len(raw) != info.file_size:
                    raise ValueError("truncated original C5 member")
                records.append(verify_model(mid, raw, catalog.get(mid, {})))
    if not seen or set(catalog) - seen:
        raise ValueError("C73 catalog model missing original C5")
    if require_full and seen != ROSTER:
        raise ValueError("expected all 730 original C5 models")
    records.sort(key=lambda row: row["model_id"])
    summary = {"schema": SCHEMA, "original_models": len(records),
               "contiguous_tail_descriptor_models": len(records),
               "source_texture_descriptors": sum(x["source_texture_descriptors"] for x in records),
               "independent_c73_anchor_models": sum(x["c73_independent_model_anchor"] for x in records),
               "c73_corrob_source_ranges": sum(x["c73_corrob_source_ranges"] for x in records),
               "missing_eof_tail_candidates": sum(len(x["candidate_missing_rows"]) for x in records),
               "verified_missing_original_pixel_bases": 0,
               "verified_gpu_sampler_roles": 0,
               "verified_p3px_conversions": 0,
               "release_ready": False}
    return {"summary": summary, "models": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--c73-csv", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(args.private_root, args.c73_csv, args.require_full)
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C277 private texture tail candidates rejected: " + str(exc) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
