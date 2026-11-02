#!/usr/bin/env python3
"""C285: compare ETC1 5-bit color expansion hypotheses against private C84.

Both bit replication and integer-floor 255/31 expansion are candidates.
Agreement with prior C84 conversion does NOT prove original GPU semantics.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from c283_private_low_bpp_candidates import audit, validate, ETC_MODIFIERS, pack
from c284_private_etc1_orientation import orientation_matches


def etc1_pixel_floor(block, x, y, alpha=15):
    """Decode ETC1 with 5-bit differential bases expanded as floor(v*255/31)."""
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
        first = [v * 255 // 31 for v in bases]
        second = [v * 255 // 31 for v in second]
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


def floor_matches(source, width, height, p3px, bits):
    """Test both ETC1/ETC1A4 vertical orientations with floor 5-bit expansion."""
    validate(source, width, height, p3px, bits)
    matches = []
    stride = 8 if bits == 4 else 16
    tiles_w = width // 8
    for flip in (True, False):
        okay = True
        for y in range(height):
            sy = height - 1 - y if flip else y
            for x in range(width):
                tile = (sy // 8) * tiles_w + x // 8
                block = ((sy % 8) // 4) * 2 + (x % 8) // 4
                off = (tile * 4 + block) * stride
                color = int.from_bytes(source[off + (8 if bits == 8 else 0):off + stride], "little")
                alpha = 15
                if bits == 8:
                    alpha_bits = int.from_bytes(source[off:off + 8], "little")
                    alpha = (alpha_bits >> (4 * ((x % 4) * 4 + sy % 4))) & 15
                try:
                    pixel = etc1_pixel_floor(color, x % 4, sy % 4, alpha)
                except ValueError:
                    okay = False
                    break
                if pixel != struct.unpack_from("<H", p3px, 10 + 2 * (y * width + x))[0]:
                    okay = False
                    break
            if not okay:
                break
        if okay:
            matches.append(("ETC1A4" if bits == 8 else "ETC1") +
                           ("_FLOOR5_FLIP_Y" if flip else "_FLOOR5_NO_FLIP_Y"))
    return tuple(matches)


def quantization_matches(source, width, height, p3px, bits):
    """Preserve every exact bit-replication/floor hypothesis and ambiguity."""
    return tuple(orientation_matches(source, width, height, p3px, bits) +
                 floor_matches(source, width, height, p3px, bits))


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
                       extra_candidate=quantization_matches)
        result["summary"]["schema"] = "C285_PRIVATE_ETC1_5BIT_EXPANSION_CANDIDATES_V1"
        write_private_report(args.output_private_json, result)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C285 private ETC1 quantization gate rejected: " + str(exc) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
