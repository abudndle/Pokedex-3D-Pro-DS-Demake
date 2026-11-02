#!/usr/bin/env python3
"""C278: private C5/C73/P3TM texture geometry and byte-density evidence.

Byte density is NOT a decoded pixel format, swizzle, GPU sampler assignment,
or proof of source pixel fidelity. No private data enters CI.
"""
import argparse
import collections
import json
import re
import stat
import struct
import zipfile
import zlib
from pathlib import Path

SCHEMA = "C278_PRIVATE_TEXTURE_FORMAT_EVIDENCE_V1"
CATALOG_MEMBER = re.compile(r"catalogs/(p\d{3})\.p3tm\Z")
MAX_CATALOG = 65536
MAX_CATALOG_TOTAL = 16 * 1024 * 1024
MAX_CATALOG_MEMBERS = 1024


def parse_catalog(raw, model_id):
    """Parse bounded P3TM v1 records, validating CRC and record extents."""
    if not isinstance(raw, bytes) or not 20 <= len(raw) <= MAX_CATALOG:
        raise ValueError("P3TM size invalid")
    magic, version, ident, count, flags, length, crc = struct.unpack_from("<4sHHHHII", raw)
    if (magic != b"P3TM" or version != 1 or model_id != f"p{ident:03d}"
            or count > 256 or flags or length != len(raw) - 20
            or zlib.crc32(raw[20:]) != crc):
        raise ValueError("P3TM header/model/CRC invalid")
    offset = 20
    records = []
    for index in range(count):
        if len(raw) - offset < 48:
            raise ValueError("P3TM truncated record")
        ident, width, height, opaque_format, source_offset = struct.unpack_from("<HHHII", raw, offset)
        digest = raw[offset + 14:offset + 46].hex()
        name_size = struct.unpack_from("<H", raw, offset + 46)[0]
        offset += 48
        if (ident != index or not 1 <= width <= 4096 or not 1 <= height <= 4096
                or not 0 < name_size <= 127 or name_size > len(raw) - offset):
            raise ValueError("P3TM texture index/dimensions/name extent invalid")
        name_bytes = raw[offset:offset + name_size]
        if any(byte < 32 or byte > 126 for byte in name_bytes):
            raise ValueError("P3TM non-ASCII source name")
        records.append({"index": index, "width": width, "height": height,
                        "opaque_format": opaque_format, "source_offset": source_offset,
                        "source_sha256": digest, "source_name": name_bytes.decode("ascii")})
        offset += name_size
    if offset != len(raw):
        raise ValueError("P3TM trailing bytes")
    return records


def byte_density(size, width, height):
    """Classify only exact storage density; never label a hardware format."""
    if not all(isinstance(x, int) and x > 0 for x in (size, width, height)):
        raise ValueError("invalid texture dimensions or byte length")
    pixels = width * height
    if (size * 8) % pixels:
        return "NONINTEGRAL_OR_PADDED"
    bits = (size * 8) // pixels
    return f"{bits}_BPP_STORAGE_ONLY" if bits in (4, 8, 16, 24, 32) else "UNKNOWN_OR_PADDED"


def verify_model(model_id, raw, catalog_raw, c73_rows):
    # Reuse existing source validators rather than guessing a new C5 layout.
    from c275_private_draw_material_chain import c75_from_source, ROSTER
    from c277_private_texture_tail_candidates import candidates
    if model_id not in ROSTER:
        raise ValueError("invalid original C5 model ID")
    source_names = c75_from_source(raw)
    source_ranges = candidates(raw)
    catalog = parse_catalog(catalog_raw, model_id)
    if len(catalog) > len(source_names) or len(source_ranges) != len(source_names):
        raise ValueError("C5/P3TM texture descriptor count mismatch")
    if set(c73_rows) != set(range(len(c73_rows))) or len(c73_rows) > len(catalog):
        raise ValueError("C73 source indices are not a prefix")
    records = []
    for idx, (start, size, digest) in enumerate(source_ranges):
        if idx >= len(catalog):
            records.append({"index": idx, "opaque_source_format": None,
                            "width": None, "height": None, "source_bytes": size,
                            "byte_density": "NO_P3TM_METADATA",
                            "c73_source_sha_anchor": False,
                            "p3tm_offset_matches_tail_candidate": False,
                            "p3tm_sha_matches_tail_candidate": False,
                            "pixel_format_decoded": False, "gpu_sampler_verified": False})
            continue
        row = catalog[idx]
        if row["source_name"] != source_names[idx]["original_texture_name"]:
            raise ValueError("C5/P3TM original texture name mismatch")
        anchored = idx in c73_rows
        if anchored and (c73_rows[idx] != (start, size, digest)
                         or row["source_offset"] != start or row["source_sha256"] != digest):
            raise ValueError("C73/P3TM source offset/SHA anchor mismatch")
        # P3TM may derive from the same C5/C73 extraction; unanchored
        # rows cannot establish independent provenance.
        records.append({"index": idx, "opaque_source_format": row["opaque_format"],
                        "width": row["width"], "height": row["height"],
                        "source_bytes": size,
                        "byte_density": byte_density(size, row["width"], row["height"]),
                        "c73_source_sha_anchor": anchored,
                        "p3tm_offset_matches_tail_candidate": row["source_offset"] == start,
                        "p3tm_sha_matches_tail_candidate": row["source_sha256"] == digest,
                        "pixel_format_decoded": False, "gpu_sampler_verified": False})
    return {"model_id": model_id, "records": records}


def audit(private_root, catalog_zip, c73_csv, require_full=False):
    from c275_private_draw_material_chain import (MEMBER, ROSTER, MAX_ENTRIES,
                                                   MAX_MODEL, MAX_TOTAL)
    from c276_private_source_texture_coverage import read_catalog
    catalog_rows = read_catalog(c73_csv)
    catalogs = {}
    consumed = 0
    with zipfile.ZipFile(catalog_zip) as archive:
        if len(archive.infolist()) > MAX_CATALOG_MEMBERS:
            raise ValueError("P3TM catalog ZIP entry budget exceeded")
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
                raise ValueError("duplicate or unexpected P3TM catalog model")
            if not 0 < info.file_size <= MAX_CATALOG or consumed + info.file_size > MAX_CATALOG_TOTAL:
                raise ValueError("P3TM catalog ZIP byte budget exceeded")
            consumed += info.file_size
            catalogs[mid] = archive.read(info)
    seen = set()
    models = []
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
                        raise ValueError("unexpected C5 source member")
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in seen or mid not in catalogs:
                    raise ValueError("duplicate/unexpected C5 or missing P3TM catalog")
                seen.add(mid)
                if not 0 < info.file_size <= MAX_MODEL or consumed + info.file_size > MAX_TOTAL:
                    raise ValueError("C5 source byte budget exceeded")
                consumed += info.file_size
                models.append(verify_model(mid, archive.read(info), catalogs[mid], catalog_rows.get(mid, {})))
    if not seen or set(catalogs) != seen or set(catalog_rows) - seen:
        raise ValueError("C5/P3TM/C73 model coverage mismatch")
    if require_full and seen != ROSTER:
        raise ValueError("expected all 730 original C5 models")
    counts = collections.Counter()
    anchored = 0
    for model in models:
        for record in model["records"]:
            counts[record["byte_density"]] += 1
            anchored += record["c73_source_sha_anchor"]
    summary = {"schema": SCHEMA, "models": len(models),
               "source_texture_descriptors": sum(counts.values()),
               "c73_sha_anchored_rows": anchored,
               "source_rows_missing_p3tm_metadata": counts["NO_P3TM_METADATA"],
               "storage_density_classes": dict(sorted(counts.items())),
               "verified_pixel_formats": 0, "verified_gpu_sampler_roles": 0,
               "verified_p3px_source_pixel_equivalence": 0,
               "asset_integrated_emulator_verified": False, "release_ready": False}
    return {"summary": summary, "models": sorted(models, key=lambda row: row["model_id"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--catalog-zip", type=Path, required=True)
    parser.add_argument("--c73-csv", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(args.private_root, args.catalog_zip, args.c73_csv, args.require_full)
        from c275_private_draw_material_chain import write_private_report
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C278 private texture format evidence rejected: " + str(exc) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
