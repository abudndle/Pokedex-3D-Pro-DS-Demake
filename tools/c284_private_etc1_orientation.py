#!/usr/bin/env python3
"""C284: private C56/C84 ETC1 vertical orientation candidate comparison.

An exact match with prior C84 P3PX is NOT independent original GPU format,
material, sampler, or asset-integrated emulator verification.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from c283_private_low_bpp_candidates import (
    audit, validate, etc1_pixel, compressed_candidate_matches)


def orientation_matches(source, width, height, p3px, bits):
    """Return all exact flipped/unflipped little-endian ETC1 hypotheses.

    Multiple matches are ambiguous, never silently assigned to a GPU format.
    """
    validate(source, width, height, p3px, bits)
    matches = []
    if compressed_candidate_matches(source, width, height, p3px, bits):
        matches.append("ETC1A4_FLIP_Y" if bits == 8 else "ETC1_FLIP_Y")
    stride = 8 if bits == 4 else 16
    tiles_w = width // 8
    for y in range(height):
        for x in range(width):
            tile = (y // 8) * tiles_w + x // 8
            block = ((y % 8) // 4) * 2 + (x % 8) // 4
            off = (tile * 4 + block) * stride
            color = int.from_bytes(source[off + (8 if bits == 8 else 0):off + stride], "little")
            alpha = 15
            if bits == 8:
                alpha_bits = int.from_bytes(source[off:off + 8], "little")
                alpha = (alpha_bits >> (4 * ((x % 4) * 4 + y % 4))) & 15
            try:
                pixel = etc1_pixel(color, x % 4, y % 4, alpha)
            except ValueError:
                return tuple(matches)
            if pixel != struct.unpack_from("<H", p3px, 10 + 2 * (y * width + x))[0]:
                return tuple(matches)
    matches.append("ETC1A4_NO_FLIP_Y" if bits == 8 else "ETC1_NO_FLIP_Y")
    return tuple(matches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--c84-zip", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    from c275_private_draw_material_chain import write_private_report
    try:
        result = audit(args.private_root, args.c84_zip, args.require_full,
                       extra_candidate=orientation_matches)
        result["summary"]["schema"] = "C284_PRIVATE_ETC1_ORIENTATION_CANDIDATES_V1"
        write_private_report(args.output_private_json, result)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C284 private ETC1 orientation gate rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
