#!/usr/bin/env python3
"""C279: original C5 header-relative texture payload base, private only.

C5 header +4 plus 0x78 matches 4,039 C73 SHA-backed ranges across 726
models. Four C73-absent models remain header-based candidates, not
independently verified. No original bytes/hashes or assets in public CI.
"""
import argparse
import collections
import hashlib
import json
import stat
import struct
import zipfile
from pathlib import Path

from c275_private_draw_material_chain import (MEMBER, ROSTER, MAX_ENTRIES,
                                               MAX_MODEL, MAX_TOTAL, c75_from_source,
                                               write_private_report)
from c276_private_source_texture_coverage import read_catalog
from c278_private_texture_format_evidence import (parse_catalog, byte_density, CATALOG_MEMBER,
                                                   MAX_CATALOG, MAX_CATALOG_TOTAL, MAX_CATALOG_MEMBERS)

SCHEMA = "C279_PRIVATE_C5_HEADER_TEXTURE_BASE_V1"


def source_ranges(raw):
    if not isinstance(raw, bytes) or not 120 <= len(raw) <= MAX_MODEL:
        raise ValueError("invalid original C5 source size")
    names = c75_from_source(raw)
    base_field = struct.unpack_from("<I", raw, 4)[0]
    base = base_field + 120
    table = struct.unpack_from("<I", raw, 0x30)[0]
    strings_at = struct.unpack_from("<I", raw, 0x64)[0]
    if base <= strings_at or base >= len(raw):
        raise ValueError("C5 header texture base outside source payload")
    expected = 0
    ranges = []
    for index in range(len(names)):
        rel, size = (struct.unpack_from("<I", raw, table + index * 28 + off)[0]
                     for off in (0, 12))
        if rel != expected or not 0 < size <= MAX_MODEL:
            raise ValueError("C5 relative texture offsets not contiguous")
        expected += size
        if expected > len(raw) - base:
            raise ValueError("C5 header texture range outside source")
        start = base + rel
        ranges.append((start, size, hashlib.sha256(raw[start:start + size]).hexdigest()))
    if not ranges:
        raise ValueError("no original C5 texture descriptors")
    return ranges


def source_descriptor_metadata(raw):
    """Recover C5 height (+16), width (+18), opaque format (+20) directly."""
    ranges = source_ranges(raw)
    table = struct.unpack_from("<I", raw, 0x30)[0]
    result = []
    for index, (start, size, digest) in enumerate(ranges):
        at = table + index * 28
        height, width = struct.unpack_from("<HH", raw, at + 16)
        fmt = struct.unpack_from("<I", raw, at + 20)[0]
        if not 1 <= width <= 4096 or not 1 <= height <= 4096:
            raise ValueError("C5 original texture dimensions invalid")
        result.append({"source_offset": start, "source_bytes": size, "source_sha256": digest,
                       "width": width, "height": height, "opaque_format": fmt,
                       "byte_density": byte_density(size, width, height)})
    return result


def verify_model(model_id, raw, indexed, p3tm_bytes=None):
    if model_id not in ROSTER:
        raise ValueError("invalid original C5 model ID")
    metadata = source_descriptor_metadata(raw)
    ranges = [(x["source_offset"], x["source_bytes"], x["source_sha256"]) for x in metadata]
    catalog = parse_catalog(p3tm_bytes, model_id) if p3tm_bytes is not None else None
    if catalog is not None and len(catalog) > len(metadata):
        raise ValueError("C5/P3TM source descriptor count mismatch")
    if set(indexed) != set(range(len(indexed))) or len(indexed) > len(ranges):
        raise ValueError("C73 source indices are not a valid prefix")
    records = []
    for index, row in enumerate(ranges):
        anchored = index in indexed
        if anchored and indexed[index] != row:
            raise ValueError("C73 original source offset/size/SHA disagrees with C5 header base")
        entry = metadata[index]
        corroborated = catalog is not None and index < len(catalog)
        if corroborated:
            c = catalog[index]
            if (entry["width"], entry["height"], entry["opaque_format"]) != (
                    c["width"], c["height"], c["opaque_format"]):
                raise ValueError("C5/P3TM original dimensions or format mismatch")
            if anchored and (c["source_offset"], c["source_sha256"]) != (row[0], row[2]):
                raise ValueError("C73/P3TM source offset/SHA mismatch")
        records.append({"index": index, **entry, "c73_sha_anchor": anchored,
                        "p3tm_metadata_corrob": corroborated,
                        "status": "C73_SOURCE_SHA_VERIFIED" if anchored else "HEADER_BASE_CANDIDATE_NOT_IN_C73"})
    return {"model_id": model_id, "source_c5_sha256": hashlib.sha256(raw).hexdigest(),
            "records": records}


def audit(private_root, c73_csv, require_full=False, catalog_zip=None):
    catalog = read_catalog(c73_csv)
    catalogs = {}
    if catalog_zip is not None:
        consumed_catalog = 0
        with zipfile.ZipFile(catalog_zip) as archive:
            if len(archive.infolist()) > MAX_CATALOG_MEMBERS:
                raise ValueError("P3TM ZIP entry budget exceeded")
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                    raise ValueError("symlinked P3TM catalog member")
                match = CATALOG_MEMBER.fullmatch(info.filename)
                if not match:
                    if info.filename.lower().endswith(".p3tm"):
                        raise ValueError("unexpected P3TM catalog member")
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in catalogs:
                    raise ValueError("duplicate or unexpected P3TM model")
                if not 0 < info.file_size <= MAX_CATALOG or consumed_catalog + info.file_size > MAX_CATALOG_TOTAL:
                    raise ValueError("P3TM ZIP byte budget exceeded")
                consumed_catalog += info.file_size
                catalogs[mid] = archive.read(info)
    seen = set()
    records = []
    consumed = 0
    for part in (1, 2, 3):
        path = Path(private_root) / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
        with zipfile.ZipFile(path) as archive:
            if len(archive.infolist()) > MAX_ENTRIES:
                raise ValueError("C5 ZIP entry budget exceeded")
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
                    raise ValueError("original C5 ZIP byte budget exceeded")
                consumed += info.file_size
                raw = archive.read(info)
                if len(raw) != info.file_size:
                    raise ValueError("truncated original C5 member")
                if catalog_zip is not None and mid not in catalogs:
                    raise ValueError("missing P3TM model catalog")
                records.append(verify_model(mid, raw, catalog.get(mid, {}), catalogs.get(mid)))
    if not seen or set(catalog) - seen or (catalog_zip is not None and set(catalogs) != seen):
        raise ValueError("C73/P3TM model missing original C5")
    if require_full and seen != ROSTER:
        raise ValueError("expected all 730 original C5 models")
    anchored = sum(row["c73_sha_anchor"] for model in records for row in model["records"])
    total = sum(len(model["records"]) for model in records)
    density = collections.Counter(row["byte_density"] for model in records for row in model["records"])
    summary = {"schema": SCHEMA, "models": len(seen),
               "source_texture_ranges_bounded": total,
               "source_sha_anchored": anchored,
               "header_base_only_unanchored": total - anchored,
               "c76_metadata_crosschecked": sum(row["p3tm_metadata_corrob"] for model in records for row in model["records"]),
               "source_format_density_classes": dict(sorted(density.items())),
               "verified_gpu_formats": 0, "verified_gpu_sampler_roles": 0,
               "verified_p3px_pixel_equivalence": 0, "release_ready": False}
    return {"summary": summary, "models": sorted(records, key=lambda row: row["model_id"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--c73-csv", type=Path, required=True)
    parser.add_argument("--catalog-zip", type=Path)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(args.private_root, args.c73_csv, args.require_full, args.catalog_zip)
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C279 private header texture base rejected: " + str(exc) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
