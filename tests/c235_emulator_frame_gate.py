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

    def changed(a, b):
        left, right_pixels = frames[a][1], frames[b][1]
        return sum(left[y * row_bytes + x * pixel_bytes:
                        y * row_bytes + x * pixel_bytes + 3] !=
                   right_pixels[y * row_bytes + x * pixel_bytes:
                                y * row_bytes + x * pixel_bytes + 3]
                   for y in range(0, height, 2) for x in range(0, width, 2))

    opened, advanced, restored = changed(0, 1), changed(1, 2), changed(0, 3)
    result = {"home_to_dex_pixels": opened,
              "dex_right_pixels": advanced,
              "after_b_pixels_different_from_home": restored}
    if opened < min_changed:
        raise ValueError(f"A did not visibly open Pokédex: {result}")
    if advanced < min_changed:
        raise ValueError(f"Right did not visibly advance Pokédex: {result}")
    if restored > max(min_changed // 2, opened // 4):
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
