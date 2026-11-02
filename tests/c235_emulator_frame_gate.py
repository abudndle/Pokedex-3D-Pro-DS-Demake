#!/usr/bin/env python3
"""C235: fail-closed, asset-free XWD evidence gate for DeSmuME Dex A/Right/B.

Compares the same pixel positions across four captured windows. The test only
proves visible menu transitions in an asset-free development ROM, not authentic
3DS rendering, original game parity, or physical DS keypad behavior.
"""
import argparse
import struct
from pathlib import Path

MAX_XWD_BYTES = 64 * 1024 * 1024


def read_xwd(path):
    data = Path(path).read_bytes()
    if not 100 <= len(data) <= MAX_XWD_BYTES:
        raise ValueError("invalid XWD file size")
    h = struct.unpack_from(">25I", data)
    header, width, height, depth, bpp, row_bytes, colors = (
        h[0], h[4], h[5], h[3], h[11], h[12], h[19])
    if (header < 100 or header > len(data) or not 1 <= width <= 4096
            or not 1 <= height <= 4096 or depth not in (24, 32)
            or bpp not in (24, 32) or row_bytes < width * (bpp // 8)
            or row_bytes > 4096 * 16 or colors > 65536):
        raise ValueError("invalid XWD image geometry")
    offset = header + colors * 12
    size = row_bytes * height
    if offset > len(data) or size > len(data) - offset:
        raise ValueError("truncated XWD pixel buffer")
    return (width, height, row_bytes, bpp // 8), memoryview(data)[offset:offset + size]


def compare_frames(home, dex, right, back, min_changed=100):
    if type(min_changed) is not int or min_changed < 1:
        raise ValueError("invalid minimum changed pixels")
    frames = [read_xwd(path) for path in (home, dex, right, back)]
    shape = frames[0][0]
    if any(frame[0] != shape for frame in frames):
        raise ValueError("XWD capture dimensions changed")
    width, height, row_bytes, pixel_bytes = shape

    if (width, height) != (256, 384):
        raise ValueError("expected native 256x384 dual-screen capture")

    def changed(a, b, region=None, step=2):
        left, right_pixels = frames[a][1], frames[b][1]
        x0, y0, x1, y1 = region or (0, 0, width, height)
        return sum(left[y * row_bytes + x * pixel_bytes:
                        y * row_bytes + x * pixel_bytes + 3] !=
                   right_pixels[y * row_bytes + x * pixel_bytes:
                                y * row_bytes + x * pixel_bytes + 3]
                   for y in range(y0, y1, step) for x in range(x0, x1, step))

    opened, advanced, restored = changed(0, 1), changed(1, 2), changed(0, 3)
    # #001->#002 changes one small number glyph on each screen. The former
    # 100-sampled-pixel Right threshold was impossible for this transition.
    # Require BOTH number glyph regions, excluding the ARM9 debug heartbeat.
    upper_number = changed(1, 2, (125, 35, 150, 60), 1)
    lower_number = changed(1, 2, (80, 288, 105, 315), 1)
    lower_restored = changed(0, 3, (0, 200, 256, 384), 2)
    result = {"home_to_dex_pixels": opened,
              "dex_right_pixels": advanced,
              "dex_upper_number_pixels": upper_number,
              "dex_lower_number_pixels": lower_number,
              "after_b_pixels_different_from_home": restored,
              "after_b_lower_pixels_different_from_home": lower_restored}
    if opened < min_changed:
        raise ValueError(f"A did not visibly open Pokédex: {result}")
    if upper_number < 10 or lower_number < 10:
        raise ValueError(f"Right did not visibly advance Pokédex on BOTH screens: {result}")
    if (restored > max(min_changed // 2, opened // 4)
            or lower_restored > max(10, opened // 10)):
        raise ValueError(f"B did not visibly return to home: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("home", type=Path)
    parser.add_argument("dex", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("back", type=Path)
    args = parser.parse_args()
    print("C235 verified asset-free DeSmuME navigation:",
          compare_frames(args.home, args.dex, args.right, args.back))


if __name__ == "__main__":
    main()
