#!/usr/bin/env python3
"""C281: 24-bpp source RGB Morton tiles to A1RGB555 P3PX differential.

Private conversion agreement only: C78 is not an independent 3DS GPU
reference. Unanchored original C5 textures are explicitly excluded.
"""
import struct
from c280_private_rgba8_pixel_equivalence import morton8


def convert_rgb8_candidate(source, width, height):
    if (not isinstance(source, bytes) or not 8 <= width <= 1024 or
            not 8 <= height <= 1024 or width % 8 or height % 8 or
            len(source) != width * height * 3 or len(source) > 4 * 1024 * 1024):
        raise ValueError("24-bpp source size or tile dimensions invalid")
    # Optional vectorization for private 1,771-texture batches; the stdlib
    # fallback remains the tested dependency-free public CI path.
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is not None:
        yy, xx = np.indices((height, width))
        yy = height - 1 - yy
        morton = np.zeros((height, width), dtype=np.int64)
        for bit in range(3):
            morton |= ((xx >> bit) & 1) << (2 * bit)
            morton |= ((yy >> bit) & 1) << (2 * bit + 1)
        idx = ((yy // 8) * (width // 8) + xx // 8) * 64 + morton
        rgb = np.frombuffer(source, dtype=np.uint8).reshape(-1, 3)[idx].astype(np.uint16)
        pixels = (0x8000 | (rgb[:, :, 2] >> 3) << 10 |
                  (rgb[:, :, 1] >> 3) << 5 | (rgb[:, :, 0] >> 3)).astype("<u2")
        return struct.pack("<4sHHH", b"P3PX", 2, width, height) + pixels.tobytes()
    out = bytearray(struct.pack("<4sHHH", b"P3PX", 2, width, height))
    out.extend(bytes(2 * width * height))
    tiles_w = width // 8
    for y in range(height):
        sy = height - 1 - y
        tile_row = (sy // 8) * tiles_w * 64
        for x in range(width):
            source_index = (tile_row + (x // 8) * 64 + morton8(x % 8, sy % 8)) * 3
            red, green, blue = source[source_index:source_index + 3]
            pixel = 0x8000 | ((blue >> 3) << 10) | ((green >> 3) << 5) | (red >> 3)
            struct.pack_into("<H", out, 10 + 2 * (y * width + x), pixel)
    return bytes(out)


def compare_rgb8_candidate(source, width, height, p3px):
    if (not isinstance(p3px, bytes) or len(p3px) < 10 or
            p3px[:4] != b"P3PX" or struct.unpack_from("<HHH", p3px, 4) != (2, width, height) or
            len(p3px) != 10 + 2 * width * height):
        raise ValueError("C78 P3PX header/dimensions/length invalid")
    if convert_rgb8_candidate(source, width, height) != p3px:
        raise ValueError("RGB8 source-to-P3PX pixel mismatch")
    return width * height


def audit(private_root, c73_csv, p3px_zip, require_full=False):
    from c280_private_rgba8_pixel_equivalence import audit as common_audit
    result = common_audit(private_root, c73_csv, p3px_zip, require_full,
                          density="24_BPP_STORAGE_ONLY", comparator=compare_rgb8_candidate,
                          schema="C281_PRIVATE_RGB8_P3PX_DIFFERENTIAL_V1", allow_unanchored=True)
    summary = result["summary"]
    summary["same_dimension_24bpp_textures_exact"] = summary.pop("same_dimension_32bpp_textures_exact")
    summary["resized_24bpp_textures_excluded"] = summary.pop("resized_32bpp_textures_excluded")
    return result


def main():
    import argparse
    import json
    import zipfile
    from pathlib import Path
    from c275_private_draw_material_chain import write_private_report
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
        p.exit(1, "C281 private RGB8 differential rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
