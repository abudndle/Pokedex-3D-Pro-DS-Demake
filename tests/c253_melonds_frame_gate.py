#!/usr/bin/env python3
"""C253: fail-closed *preliminary* melonDS window/dual-screen color gate.

A Qt window with color variation does not by itself prove that the ROM booted,
that the two DS screens are correctly mapped, or that DSi camera works. A real
capture and manual inspection remain required before acceptance.
"""
from pathlib import Path
import struct
import sys

MAX_XWD = 64 * 1024 * 1024


def inspect(path):
    data = Path(path).read_bytes()
    if not 100 <= len(data) <= MAX_XWD:
        raise ValueError("invalid melonDS XWD size")
    h = struct.unpack_from(">25I", data)
    header, width, height, depth, bpp, row, colors = (
        h[0], h[4], h[5], h[3], h[11], h[12], h[19])
    if (not 100 <= header <= len(data) or not 256 <= width <= 2048 or
            not 384 <= height <= 2048 or depth not in (24, 32) or
            bpp not in (24, 32) or row < width * (bpp // 8) or
            row > 2048 * 16 or colors > 65536):
        raise ValueError("invalid melonDS XWD window geometry")
    offset = header + colors * 12
    size = row * height
    if offset > len(data) or size > len(data) - offset:
        raise ValueError("truncated melonDS XWD pixels")
    pixels = memoryview(data)[offset:offset + size]
    stride = bpp // 8
    unique = [set(), set()]
    nonblack = 0
    total = 0
    for y in range(0, height, 8):
        for x in range(0, width, 8):
            rgb = bytes(pixels[y * row + x * stride:y * row + x * stride + 3])
            unique[int(y >= height // 2)].add(rgb)
            nonblack += max(rgb) > 16
            total += 1
    ratio = nonblack / total
    if ratio < 0.05 or any(len(part) < 2 for part in unique):
        raise ValueError("melonDS window mostly blank or single-color half")
    return {"width": width, "height": height, "nonblack_ratio": round(ratio, 3),
            "upper_colors": len(unique[0]), "lower_colors": len(unique[1]),
            "rom_boot_verified": False, "dsi_verified": False,
            "original_assets_verified": False}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c253_melonds_frame_gate.py CAPTURE.xwd")
    print("C253 preliminary melonDS visual evidence:", inspect(sys.argv[1]))
