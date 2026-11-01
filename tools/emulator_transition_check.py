#!/usr/bin/env python3
"""Fail-closed DeSmuME asset-free development-ROM navigation evidence.

Compares real XWD capture pixels, not OCR or inferred game state.
"""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path

WIDTH, HEIGHT = 256, 384


def load_xwd(path: Path):
    raw = path.read_bytes()
    if len(raw) < 100:
        raise ValueError(f'{path}: truncated XWD header')
    head = struct.unpack_from('>25I', raw)
    header, version, pixmap, depth, width, height = head[:6]
    byte_order, bits_per_pixel, bytes_per_line, ncolors = head[7], head[11], head[12], head[19]
    if (version != 7 or pixmap != 2 or (width, height) != (WIDTH, HEIGHT)
            or depth not in (24, 32) or bits_per_pixel not in (24, 32)
            or byte_order not in (0, 1) or header < 100
            or bytes_per_line < WIDTH * (bits_per_pixel // 8)
            or bytes_per_line > WIDTH * 8 or ncolors > 256):
        raise ValueError(f'{path}: unsupported or invalid DeSmuME XWD header')
    start = header + ncolors * 12
    end = start + bytes_per_line * HEIGHT
    if end != len(raw):
        raise ValueError(f'{path}: XWD size/stride mismatch')
    pixels = raw[start:end]
    stride = bits_per_pixel // 8
    return [b''.join(pixels[y * bytes_per_line + x * stride:
                            y * bytes_per_line + x * stride + 3]
                     for x in range(WIDTH))
            for y in range(HEIGHT)]


def differences(a, b):
    if len(a) != HEIGHT or len(b) != HEIGHT:
        raise ValueError('invalid frame dimensions')
    return [sum(a[y][x:x+3] != b[y][x:x+3]
                for x in range(0, WIDTH * 3, 3))
            for y in range(HEIGHT)]


def verify(home, opened, browsed, returned):
    h, d, r, b = map(load_xwd, (home, opened, browsed, returned))
    entered = differences(h, d)
    moved = differences(d, r)
    restored = differences(h, b)
    exited = differences(r, b)
    entry_count = sum(entered)
    browse_count = sum(moved)
    exit_count = sum(exited)
    return_count = sum(restored)
    lower_browse = sum(moved[192:])
    lower_enter = sum(entered[192:])
    lower_exit = sum(exited[192:])
    report = {'home_to_dex_changed_pixels': entry_count,
              'dex_to_next_changed_pixels': browse_count,
              'dex_lower_screen_changed_pixels': lower_browse,
              'dex_to_home_changed_pixels': exit_count,
              'dex_to_home_lower_screen_changed_pixels': lower_exit,
              'home_return_changed_pixels': return_count}
    print(json.dumps(report, sort_keys=True))
    if entry_count < 200 or lower_enter < 80:
        raise AssertionError('A did not visibly open the Pokédex page')
    if lower_browse < 8:
        raise AssertionError('Right did not visibly change the Pokédex lower-screen entry')
    if exit_count < 200 or lower_exit < 80:
        raise AssertionError('B did not visibly return from Pokédex to the home menu')
    if return_count > max(1500, entry_count // 2):
        raise AssertionError('After B the display does not sufficiently resemble the home menu')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home', type=Path, required=True)
    p.add_argument('--dex', type=Path, required=True)
    p.add_argument('--next', dest='next_entry', type=Path, required=True)
    p.add_argument('--returned', type=Path, required=True)
    args = p.parse_args()
    verify(args.home, args.dex, args.next_entry, args.returned)


if __name__ == '__main__':
    main()
