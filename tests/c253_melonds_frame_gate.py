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


def compare_touch(home, dex):
    a = inspect(home)
    b = inspect(dex)
    if (a["width"], a["height"]) != (b["width"], b["height"]):
        raise ValueError("melonDS capture geometry changed")
    def pixels(path):
        data = Path(path).read_bytes()
        h = struct.unpack_from(">25I", data)
        offset = h[0] + h[19] * 12
        return memoryview(data)[offset:offset + h[12] * h[5]], h[12], h[11] // 8
    frame_a, row, stride = pixels(home)
    frame_b, _, _ = pixels(dex)
    width, height = a["width"], a["height"]
    def delta(y0, y1):
        return sum(
            frame_a[y * row + x * stride:y * row + x * stride + 3] !=
            frame_b[y * row + x * stride:y * row + x * stride + 3]
            for y in range(y0, min(y1, height), 2)
            for x in range(64, min(200, width), 2)
        )
    upper = delta(35, 175)
    lower = delta(max(height // 2 + 40, 250), height - 12)
    if upper < 30 or lower < 30:
        raise ValueError(f"melonDS touch did not change both DS screens: {upper}/{lower}")
    return {"upper_changed_samples": upper, "lower_changed_samples": lower,
            "real_touch_frame_delta_verified": True,
            "original_asset_rendering_verified": False,
            "dsi_camera_verified": False}


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: c253_melonds_frame_gate.py HOME.xwd [DEX.xwd]")
    print("C253 preliminary melonDS visual evidence:", inspect(sys.argv[1]))
    if len(sys.argv) == 3:
        print("C253 real touch dual-screen delta:", compare_touch(*sys.argv[1:]))
