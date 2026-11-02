#!/usr/bin/env python3
"""C283 private C56/C84 low-bpp candidate differential; no original assets in Git.

A matching C84 conversion is not independent proof of PICA200 format,
shader, sampler, or hardware rendering. Never infer GPU format from bpp.
"""
import argparse
import collections
import hashlib
import json
import re
import stat
import struct
import zipfile
from pathlib import Path

SCHEMA = "C283_PRIVATE_LOW_BPP_C84_CANDIDATES_V1"
MAX_P3PX = 4 * 1024 * 1024
P3PX_MEMBER = re.compile(r"textures/(p\d{3})/t(\d{3})\.p3px\Z")
CATALOG_MEMBER = re.compile(r"catalogs/(p\d{3})\.p3tm\Z")
ETC_MODIFIERS = ((2, 8), (5, 17), (9, 29), (13, 42),
                 (18, 60), (24, 80), (33, 106), (47, 183))


def morton8(x, y):
    return sum((((x >> bit) & 1) << (2 * bit)) |
               (((y >> bit) & 1) << (2 * bit + 1)) for bit in range(3))


def pack(a, r, g, b):
    return ((int(a) & 1) << 15) | ((int(b) & 31) << 10) | ((int(g) & 31) << 5) | (int(r) & 31)


def expand4(value):
    return (value << 1) | (value >> 3)


def decode_8(name, value):
    if name == "L8":
        v = value >> 3
        return pack(1, v, v, v)
    if name == "A8":
        return pack(value >= 128, 31, 31, 31)
    if name in ("LA44_L_LOW", "LA44_L_HIGH"):
        low = name.endswith("LOW")
        v = expand4((value & 15) if low else (value >> 4))
        a = (value >> 4) if low else (value & 15)
        return pack(a >= 8, v, v, v)
    raise ValueError("unknown 8-bpp candidate")


def decode_4(name, value):
    if name.startswith("L4_"):
        v = expand4(value)
        return pack(1, v, v, v)
    if name.startswith("A4_"):
        return pack(value >= 8, 31, 31, 31)
    raise ValueError("unknown 4-bpp candidate")


CANDIDATES_8 = ("L8", "A8", "LA44_L_LOW", "LA44_L_HIGH")
CANDIDATES_4 = ("L4_LOW_FIRST", "L4_HIGH_FIRST", "A4_LOW_FIRST", "A4_HIGH_FIRST")


def validate(source, width, height, p3px, bits):
    if (type(source) is not bytes or type(p3px) is not bytes or
            type(width) is not int or type(height) is not int or bits not in (4, 8) or
            not 8 <= width <= 1024 or not 8 <= height <= 1024 or
            width % 8 or height % 8 or width * height * 2 > MAX_P3PX or
            len(source) != width * height * bits // 8):
        raise ValueError("source size or tile dimensions invalid")
    if (len(p3px) != 10 + width * height * 2 or p3px[:4] != b"P3PX" or
            struct.unpack_from("<HHH", p3px, 4) != (2, width, height)):
        raise ValueError("P3PX header/dimensions/length invalid")


def candidate_matches(source, width, height, p3px, bits):
    """Return all exact hypotheses; zero/ambiguous matches are unverified."""
    validate(source, width, height, p3px, bits)
    remaining = list(CANDIDATES_8 if bits == 8 else CANDIDATES_4)
    for y in range(height):
        sy = height - 1 - y
        for x in range(width):
            texel = ((sy // 8) * (width // 8) + x // 8) * 64 + morton8(x % 8, sy % 8)
            expected = struct.unpack_from("<H", p3px, 10 + 2 * (y * width + x))[0]
            if bits == 8:
                remaining = [name for name in remaining if decode_8(name, source[texel]) == expected]
            else:
                byte = source[texel // 2]
                remaining = [name for name in remaining if decode_4(
                    name, ((byte >> 4) if ((texel % 2 == 0) == name.endswith("HIGH_FIRST")) else byte) & 15
                ) == expected]
            if not remaining:
                return ()
    return tuple(sorted(remaining))


def etc1_pixel(block, x, y, alpha=15):
    if not 0 <= block < (1 << 64) or not 0 <= x < 4 or not 0 <= y < 4:
        raise ValueError("invalid ETC1 block/texel")
    differential = (block >> 33) & 1
    horizontal = (block >> 32) & 1
    if differential:
        bases = [(block >> shift) & 31 for shift in (59, 51, 43)]
        delta = [(block >> shift) & 7 for shift in (56, 48, 40)]
        second = [v + (d - 8 if d >= 4 else d) for v, d in zip(bases, delta)]
        if any(not 0 <= v <= 31 for v in second):
            raise ValueError("ETC1 differential color overflow")
        first = [(v << 3) | (v >> 2) for v in bases]
        second = [(v << 3) | (v >> 2) for v in second]
    else:
        first = [((block >> shift) & 15) * 17 for shift in (60, 52, 44)]
        second = [((block >> shift) & 15) * 17 for shift in (56, 48, 40)]
    half = (y >= 2) if horizontal else (x >= 2)
    color = second if half else first
    table = ETC_MODIFIERS[(block >> (34 if half else 37)) & 7]
    bit = x * 4 + y
    modifier = table[(block >> bit) & 1]
    if (block >> (bit + 16)) & 1:
        modifier = -modifier
    channels = [max(0, min(255, value + modifier)) >> 3 for value in color]
    return pack(alpha >= 8, *channels)


def compressed_candidate_matches(source, width, height, p3px, bits):
    """Hypothesis: little-endian ETC1/ETC1A4 4x4 blocks in 8x8 tiles."""
    validate(source, width, height, p3px, bits)
    block_size = 8 if bits == 4 else 16
    for y in range(height):
        sy = height - 1 - y
        for x in range(width):
            tile = (sy // 8) * (width // 8) + x // 8
            block = ((sy % 8) // 4) * 2 + (x % 8) // 4
            offset = (tile * 4 + block) * block_size
            if bits == 8:
                alpha = int.from_bytes(source[offset:offset + 8], "little")
                color = int.from_bytes(source[offset + 8:offset + 16], "little")
                a4 = (alpha >> (4 * ((x % 4) * 4 + sy % 4))) & 15
            else:
                color = int.from_bytes(source[offset:offset + 8], "little")
                a4 = 15
            try:
                pixel = etc1_pixel(color, x % 4, sy % 4, a4)
            except ValueError:
                return ()
            if pixel != struct.unpack_from("<H", p3px, 10 + 2 * (y * width + x))[0]:
                return ()
    return ("ETC1_LE_3DS_TILE" if bits == 4 else "ETC1A4_LE_3DS_TILE",)


def audit(private_root, c84_zip, require_full=False):
    from c275_private_draw_material_chain import MEMBER, ROSTER, MAX_ENTRIES, MAX_MODEL, MAX_TOTAL
    from c279_private_header_texture_base import source_descriptor_metadata
    from c278_private_texture_format_evidence import parse_catalog, MAX_CATALOG
    counts, layouts, unresolved = collections.Counter(), collections.Counter(), collections.Counter()
    records = []
    with zipfile.ZipFile(c84_zip) as prior:
        if len(prior.infolist()) > 8192:
            raise ValueError("C84 archive entry budget exceeded")
        available, catalogs, names = {}, {}, set()
        for info in prior.infolist():
            if info.is_dir():
                continue
            if info.filename in names or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError("duplicate or symlinked C84 archive member")
            names.add(info.filename)
            texture = P3PX_MEMBER.fullmatch(info.filename)
            catalog = CATALOG_MEMBER.fullmatch(info.filename)
            if texture:
                if not 10 <= info.file_size <= MAX_P3PX:
                    raise ValueError("C84 P3PX byte budget exceeded")
                available[(texture.group(1), int(texture.group(2)))] = info
            elif catalog:
                if not 20 <= info.file_size <= MAX_CATALOG:
                    raise ValueError("C84 P3TM byte budget exceeded")
                catalogs[catalog.group(1)] = info
            elif info.filename.lower().endswith((".p3px", ".p3tm")):
                raise ValueError("unexpected C84 texture/catalog member")
        if len(available) > 8192:
            raise ValueError("C84 P3PX count budget exceeded")
        seen, consumed = set(), 0
        for part in (1, 2, 3):
            path = Path(private_root) / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
            with zipfile.ZipFile(path) as archive:
                if len(archive.infolist()) > MAX_ENTRIES:
                    raise ValueError("C56 archive entry budget exceeded")
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                        raise ValueError("symlinked C56 source member")
                    match = MEMBER.fullmatch(info.filename)
                    if not match:
                        if info.filename.lower().endswith(".c5"):
                            raise ValueError("unexpected C56 C5 source member")
                        continue
                    mid = match.group(1)
                    if mid not in ROSTER or mid in seen or mid not in catalogs:
                        raise ValueError("duplicate/unknown C56 model or missing C84 catalog")
                    seen.add(mid)
                    if not 0 < info.file_size <= MAX_MODEL or consumed + info.file_size > MAX_TOTAL:
                        raise ValueError("C56 source byte budget exceeded")
                    consumed += info.file_size
                    raw = archive.read(info)
                    metadata = source_descriptor_metadata(raw)
                    cat_rows = parse_catalog(prior.read(catalogs[mid]), mid)
                    if len(cat_rows) > len(metadata):
                        raise ValueError("C5/P3TM descriptor count mismatch")
                    for index, row in enumerate(metadata):
                        if row["byte_density"] not in ("8_BPP_STORAGE_ONLY", "4_BPP_STORAGE_ONLY"):
                            continue
                        bits = int(row["byte_density"].split("_")[0])
                        counts[f"{bits}bpp_source_descriptors"] += 1
                        if index >= len(cat_rows):
                            counts["unanchored_excluded"] += 1
                            continue
                        anchor = cat_rows[index]
                        if (anchor["width"], anchor["height"], anchor["opaque_format"],
                                anchor["source_offset"], anchor["source_sha256"]) != (
                                row["width"], row["height"], row["opaque_format"],
                                row["source_offset"], row["source_sha256"]):
                            raise ValueError("original C5/C84 P3TM source SHA/format mismatch")
                        if (mid, index) not in available:
                            counts["missing_C84_conversion_excluded"] += 1
                            continue
                        data = prior.read(available[(mid, index)])
                        if len(data) < 10 or data[:4] != b"P3PX":
                            raise ValueError("invalid C84 P3PX header")
                        version, width, height = struct.unpack_from("<HHH", data, 4)
                        if version != 2 or len(data) != 10 + 2 * width * height:
                            raise ValueError("invalid C84 P3PX version/length")
                        if (width, height) != (row["width"], row["height"]):
                            counts["resized_excluded"] += 1
                            continue
                        start, size = row["source_offset"], row["source_bytes"]
                        if (start < 0 or start + size > len(raw) or
                                hashlib.sha256(raw[start:start + size]).hexdigest() != row["source_sha256"]):
                            raise ValueError("C56 source payload SHA mismatch")
                        if width % 8 or height % 8 or not 8 <= width <= 1024 or not 8 <= height <= 1024:
                            counts["unsupported_tile_dimensions_excluded"] += 1
                            continue
                        source = raw[start:start + size]
                        matches = candidate_matches(source, width, height, data, bits)
                        if not matches:
                            matches = compressed_candidate_matches(source, width, height, data, bits)
                        if len(matches) == 1:
                            status = "unique_candidate_consistent_with_C84"
                            layouts[matches[0]] += 1
                            counts["candidate_agreement_pixels"] += width * height
                        elif matches:
                            status = "ambiguous_candidates_not_verified"
                        else:
                            status = "no_supported_candidate_not_verified"
                            unresolved[f"0x{row['opaque_format']:08x}"] += 1
                        counts[status] += 1
                        records.append({"model_id": mid, "texture_index": index,
                                        "storage_bits_per_pixel": bits, "status": status,
                                        "candidates": matches, "independent_gpu_format_verified": False})
        if not seen or set(catalogs) != seen:
            raise ValueError("C56/C84 catalog model coverage mismatch")
        if require_full and seen != ROSTER:
            raise ValueError("expected all 730 original C5 models")
    return {"summary": {"schema": SCHEMA, "models": len(seen),
                        "counts": dict(sorted(counts.items())),
                        "unique_candidate_layouts": dict(sorted(layouts.items())),
                        "unresolved_source_format_words": dict(sorted(unresolved.items())),
                        "compressed_formats_tested_as_candidates": True,
                        "independent_gpu_format_verified": False,
                        "source_sampler_roles_verified": 0,
                        "asset_integrated_emulator_verified": False,
                        "release_ready": False}, "textures": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--c84-zip", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    from c275_private_draw_material_chain import write_private_report
    try:
        result = audit(args.private_root, args.c84_zip, args.require_full)
        write_private_report(args.output_private_json, result)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C283 private low-bpp candidate gate rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
