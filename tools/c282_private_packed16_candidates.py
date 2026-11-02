#!/usr/bin/env python3
"""C282: bounded private 16-bpp C5/C73-to-C78 P3PX *candidate* comparison.

Agreement with C78 is NOT independent proof of PICA200 format, sampler
binding, or authentic 3DS/DS appearance. Proprietary input/output is private.
"""
import argparse
import collections
import json
import re
import stat
import struct
import zipfile
from pathlib import Path

MAX_TEXTURES = 8192
MAX_P3PX = 4 * 1024 * 1024


def morton8(x, y):
    return sum((((x >> bit) & 1) << (2 * bit)) |
               (((y >> bit) & 1) << (2 * bit + 1)) for bit in range(3))


SCHEMA = "C282_PRIVATE_PACKED16_P3PX_CANDIDATES_V1"
TEXTURE_MEMBER = re.compile(r"textures/(p\d{3})/t\d{3}\.p3px\Z")


def pack(a, r, g, b):
    return ((a & 1) << 15) | ((b & 31) << 10) | ((g & 31) << 5) | (r & 31)


def rgb565(word):
    return pack(1, (word >> 11) & 31, ((word >> 5) & 63) >> 1, word & 31)


def bgr565(word):
    return pack(1, word & 31, ((word >> 5) & 63) >> 1, (word >> 11) & 31)


def argb1555(word):
    return pack(word >> 15, (word >> 10) & 31, (word >> 5) & 31, word & 31)


def abgr1555(word):
    return pack(word >> 15, word & 31, (word >> 5) & 31, (word >> 10) & 31)


def rgba5551(word):
    return pack(word & 1, (word >> 11) & 31, (word >> 6) & 31, (word >> 1) & 31)


def bgra5551(word):
    return pack(word & 1, (word >> 1) & 31, (word >> 6) & 31, (word >> 11) & 31)


def expand4(n):
    return (n << 1) | (n >> 3)


def rgba4444(word):
    return pack((word & 15) >= 8, expand4((word >> 12) & 15),
                expand4((word >> 8) & 15), expand4((word >> 4) & 15))


def abgr4444(word):
    return pack((word >> 12) >= 8, expand4(word & 15),
                expand4((word >> 4) & 15), expand4((word >> 8) & 15))


def la88(word):
    luminance = (word & 255) >> 3
    return pack((word >> 8) >= 128, luminance, luminance, luminance)


def al88(word):
    luminance = (word >> 8) >> 3
    return pack((word & 255) >= 128, luminance, luminance, luminance)


CANDIDATES = {
    "RGB565_R_HIGH": rgb565, "BGR565_B_HIGH": bgr565,
    "ARGB1555_A_HIGH": argb1555, "ABGR1555_A_HIGH": abgr1555,
    "RGBA5551_A_LOW": rgba5551, "BGRA5551_A_LOW": bgra5551,
    "RGBA4444_A_LOW": rgba4444, "ABGR4444_A_HIGH": abgr4444,
    "L8_A8": la88, "A8_L8": al88,
}


def candidate_matches(source, width, height, p3px):
    """Return all exact candidate names; zero/ambiguous are NOT verified."""
    if (not isinstance(source, bytes) or not isinstance(p3px, bytes) or
            not isinstance(width, int) or not isinstance(height, int) or
            not 8 <= width <= 1024 or not 8 <= height <= 1024 or
            width % 8 or height % 8 or width * height * 2 > MAX_P3PX or
            len(source) != width * height * 2):
        raise ValueError("16-bpp source size or tile dimensions invalid")
    if (len(p3px) != 10 + width * height * 2 or p3px[:4] != b"P3PX" or
            struct.unpack_from("<HHH", p3px, 4) != (2, width, height)):
        raise ValueError("C78 P3PX header/dimensions/length invalid")
    remaining = dict(CANDIDATES)
    tiles_w = width // 8
    for y in range(height):
        sy = height - 1 - y
        tile_row = (sy // 8) * tiles_w * 64
        for x in range(width):
            offset = 2 * (tile_row + (x // 8) * 64 + morton8(x % 8, sy % 8))
            word = struct.unpack_from("<H", source, offset)[0]
            expected = struct.unpack_from("<H", p3px, 10 + 2 * (y * width + x))[0]
            for name, decode in tuple(remaining.items()):
                if decode(word) != expected:
                    del remaining[name]
            if not remaining:
                return ()
    return tuple(sorted(remaining))


def audit(private_root, c73_csv, p3px_zip, require_full=False):
    from c275_private_draw_material_chain import (MEMBER, ROSTER, MAX_ENTRIES,
                                                   MAX_MODEL, MAX_TOTAL)
    from c276_private_source_texture_coverage import read_catalog
    from c279_private_header_texture_base import source_descriptor_metadata
    catalog = read_catalog(c73_csv)
    available = {}
    with zipfile.ZipFile(p3px_zip) as textures:
        infos = textures.infolist()
        if len(infos) > MAX_TEXTURES:
            raise ValueError("C78 texture ZIP entry budget exceeded")
        for info in infos:
            if info.is_dir():
                continue
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError("symlinked C78 member")
            if info.filename == "README.txt":
                continue
            if (not TEXTURE_MEMBER.fullmatch(info.filename) or
                    info.filename in available or not 10 <= info.file_size <= MAX_P3PX):
                raise ValueError("unexpected, duplicate or over-budget C78 texture")
            available[info.filename] = info
        seen = set()
        source_total = 0
        counts = collections.Counter()
        unique_layouts = collections.Counter()
        records = []
        for part in (1, 2, 3):
            path = Path(private_root) / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
            with zipfile.ZipFile(path) as archive:
                if len(archive.infolist()) > MAX_ENTRIES:
                    raise ValueError("C5 ZIP entry budget exceeded")
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                        raise ValueError("symlinked C5 source member")
                    match = MEMBER.fullmatch(info.filename)
                    if not match:
                        if info.filename.lower().endswith(".c5"):
                            raise ValueError("unexpected C5 source member")
                        continue
                    mid = match.group(1)
                    if mid not in ROSTER or mid in seen:
                        raise ValueError("duplicate or invalid C5 model")
                    seen.add(mid)
                    if not 0 < info.file_size <= MAX_MODEL or source_total + info.file_size > MAX_TOTAL:
                        raise ValueError("C5 ZIP byte budget exceeded")
                    source_total += info.file_size
                    raw = archive.read(info)
                    for index, row in enumerate(source_descriptor_metadata(raw)):
                        if row["byte_density"] != "16_BPP_STORAGE_ONLY":
                            continue
                        if index not in catalog.get(mid, {}):
                            counts["unanchored_excluded"] += 1
                            continue
                        if catalog[mid][index] != (row["source_offset"], row["source_bytes"], row["source_sha256"]):
                            raise ValueError("original C73 source SHA mismatch")
                        name = f"textures/{mid}/t{index:03d}.p3px"
                        if name not in available:
                            raise ValueError("missing C78 P3PX texture")
                        with textures.open(available[name]) as f:
                            header = f.read(10)
                        if len(header) != 10 or header[:4] != b"P3PX":
                            raise ValueError("invalid C78 P3PX header")
                        version, width, height = struct.unpack_from("<HHH", header, 4)
                        if version != 2:
                            raise ValueError("invalid C78 P3PX version")
                        if (width, height) != (row["width"], row["height"]):
                            counts["resized_excluded"] += 1
                            continue
                        start, size = row["source_offset"], row["source_bytes"]
                        matches = candidate_matches(raw[start:start + size], width, height,
                                                    textures.read(available[name]))
                        if len(matches) == 1:
                            status = "unique_candidate_agrees_with_C78"
                            unique_layouts[matches[0]] += 1
                            counts["candidate_agreement_pixels"] += width * height
                        elif matches:
                            status = "ambiguous_candidates_not_verified"
                        else:
                            status = "no_supported_candidate_not_verified"
                        counts[status] += 1
                        records.append({"model_id": mid, "texture_index": index,
                                        "status": status, "candidate_names": matches,
                                        "source_sha_anchored": True,
                                        "independent_gpu_format_verified": False})
        if not seen or set(catalog) - seen:
            raise ValueError("C73 source model missing original C5")
        if require_full and seen != ROSTER:
            raise ValueError("expected all 730 original C5 models")
    return {"summary": {"schema": SCHEMA, "models": len(seen),
                        "counts": dict(sorted(counts.items())),
                        "unique_candidate_layouts": dict(sorted(unique_layouts.items())),
                        "independent_gpu_format_verified": False,
                        "source_sampler_roles_verified": 0,
                        "asset_integrated_emulator_verified": False,
                        "release_ready": False}, "textures": records}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-root", type=Path, required=True)
    p.add_argument("--c73-csv", type=Path, required=True)
    p.add_argument("--p3px-zip", type=Path, required=True)
    p.add_argument("--output-private-json", type=Path, required=True)
    p.add_argument("--require-full", action="store_true")
    args = p.parse_args()
    from c275_private_draw_material_chain import write_private_report
    try:
        result = audit(args.private_root, args.c73_csv, args.p3px_zip, args.require_full)
        write_private_report(args.output_private_json, result)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        p.exit(1, "C282 private 16-bpp candidate gate rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
