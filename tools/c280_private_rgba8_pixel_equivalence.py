#!/usr/bin/env python3
"""C280: private 32-bpp source C5 -> C78 P3PX exact-pixel differential.

This verifies agreement with a prior original-derived conversion, NOT an
independent original GPU sampler/texture unit or 3DS screenshot reference.
No source pixels, hashes, screenshots or private ZIPs enter public CI.
"""
import argparse
import json
import stat
import struct
import zipfile
from pathlib import Path

from c275_private_draw_material_chain import (MEMBER, ROSTER, MAX_ENTRIES,
                                               MAX_MODEL, MAX_TOTAL, write_private_report)
from c276_private_source_texture_coverage import read_catalog
from c279_private_header_texture_base import source_descriptor_metadata

SCHEMA = "C280_PRIVATE_RGBA8_P3PX_DIFFERENTIAL_V1"
MAX_P3PX = 4 * 1024 * 1024
MAX_TEXTURES = 8192


def morton8(x, y):
    return sum((((x >> bit) & 1) << (2 * bit)) |
               (((y >> bit) & 1) << (2 * bit + 1)) for bit in range(3))


def convert_candidate(source, width, height):
    """Source A,R,G,B bytes, Morton 8x8 tiles, vertical flip -> A1RGB555."""
    if (not isinstance(source, bytes) or not 8 <= width <= 1024 or
            not 8 <= height <= 1024 or width % 8 or height % 8 or
            len(source) != width * height * 4 or len(source) > MAX_P3PX):
        raise ValueError("32-bpp source texture size or tile dimensions invalid")
    output = bytearray(struct.pack("<4sHHH", b"P3PX", 2, width, height))
    output.extend(bytes(width * height * 2))
    tiles_w = width // 8
    for y in range(height):
        sy = height - 1 - y
        tile_row = (sy // 8) * tiles_w * 64
        for x in range(width):
            source_index = (tile_row + (x // 8) * 64 + morton8(x % 8, sy % 8)) * 4
            alpha, red, green, blue = source[source_index:source_index + 4]
            pixel = ((alpha >= 128) << 15) | ((blue >> 3) << 10) | ((green >> 3) << 5) | (red >> 3)
            struct.pack_into("<H", output, 10 + 2 * (y * width + x), pixel)
    return bytes(output)


def compare_candidate(source, width, height, p3px):
    if (not isinstance(p3px, bytes) or len(p3px) < 10 or
            p3px[:4] != b"P3PX" or struct.unpack_from("<HHH", p3px, 4) != (2, width, height) or
            len(p3px) != 10 + 2 * width * height):
        raise ValueError("C78 P3PX header/dimensions/length invalid")
    if convert_candidate(source, width, height) != p3px:
        raise ValueError("source-to-P3PX pixel mismatch")
    return width * height


def audit(private_root, c73_csv, p3px_zip, require_full=False, *,
          density="32_BPP_STORAGE_ONLY", comparator=compare_candidate, schema=SCHEMA,
          allow_unanchored=False):
    catalog = read_catalog(c73_csv)
    with zipfile.ZipFile(p3px_zip) as textures:
        infos = textures.infolist()
        if len(infos) > MAX_TEXTURES:
            raise ValueError("C78 texture ZIP entry budget exceeded")
        available = {}
        for info in infos:
            if info.is_dir():
                continue
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError("symlinked C78 texture member")
            if info.filename == "README.txt":
                continue
            if not info.filename.startswith("textures/") or not info.filename.endswith(".p3px"):
                raise ValueError("unexpected C78 texture ZIP member")
            if info.filename in available or not 10 <= info.file_size <= MAX_P3PX:
                raise ValueError("duplicate or over-budget C78 texture")
            available[info.filename] = info
        seen = set()
        consumed = 0
        matched = resized = pixel_count = unanchored = 0
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
                        raise ValueError("symlinked original C5 member")
                    match = MEMBER.fullmatch(info.filename)
                    if not match:
                        if info.filename.lower().endswith(".c5"):
                            raise ValueError("unexpected C5 source member")
                        continue
                    mid = match.group(1)
                    if mid not in ROSTER or mid in seen:
                        raise ValueError("duplicate or invalid original C5 model")
                    seen.add(mid)
                    if not 0 < info.file_size <= MAX_MODEL or consumed + info.file_size > MAX_TOTAL:
                        raise ValueError("C5 ZIP byte budget exceeded")
                    consumed += info.file_size
                    raw = archive.read(info)
                    metadata = source_descriptor_metadata(raw)
                    for index, row in enumerate(metadata):
                        if row["byte_density"] != density:
                            continue
                        if index not in catalog.get(mid, {}):
                            if allow_unanchored:
                                unanchored += 1
                                continue
                            raise ValueError("source C5 texture lacks independent C73 SHA anchor")
                        if catalog[mid][index] != (row["source_offset"], row["source_bytes"], row["source_sha256"]):
                            raise ValueError("32-bpp original C73 source SHA mismatch")
                        name = f"textures/{mid}/t{index:03d}.p3px"
                        if name not in available:
                            raise ValueError("missing C78 32-bpp converted texture")
                        with textures.open(available[name]) as f:
                            header = f.read(10)
                        if len(header) != 10 or header[:4] != b"P3PX":
                            raise ValueError("invalid C78 P3PX header")
                        version, width, height = struct.unpack_from("<HHH", header, 4)
                        if version != 2:
                            raise ValueError("invalid C78 P3PX version")
                        if (width, height) != (row["width"], row["height"]):
                            resized += 1
                            continue  # No exact-pixel claim after lossy resizing.
                        source = raw[row["source_offset"]:row["source_offset"] + row["source_bytes"]]
                        pixels = comparator(source, width, height, textures.read(available[name]))
                        matched += 1
                        pixel_count += pixels
                        records.append({"model_id": mid, "texture_index": index,
                                        "exact_source_to_c78_p3px_pixels": pixels,
                                        "source_sha_anchored": True,
                                        "independent_3ds_gpu_decode_verified": False})
        if not seen or set(catalog) - seen:
            raise ValueError("C73 model missing original C5")
        if require_full and seen != ROSTER:
            raise ValueError("expected all 730 original C5 models")
    summary = {"schema": schema, "models": len(seen),
               "same_dimension_32bpp_textures_exact": matched,
               "exact_a1rgb555_pixels": pixel_count,
               "resized_32bpp_textures_excluded": resized,
               "unanchored_source_textures_excluded": unanchored,
               "independent_3ds_gpu_format_verified": False,
               "original_sampler_roles_verified": 0,
               "asset_integrated_emulator_verified": False, "release_ready": False}
    return {"summary": summary, "textures": records}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-root", type=Path, required=True)
    p.add_argument("--c73-csv", type=Path, required=True)
    p.add_argument("--p3px-zip", type=Path, required=True)
    p.add_argument("--output-private-json", type=Path, required=True)
    p.add_argument("--require-full", action="store_true")
    a = p.parse_args()
    try:
        result = audit(a.private_root, a.c73_csv, a.p3px_zip, a.require_full)
        write_private_report(a.output_private_json, result)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        p.exit(1, "C280 private RGBA8 differential rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
