#!/usr/bin/env python3
"""C254: strict asset-free melonDS 1.1 Pokédex Right/B frame acceptance.

A screenshot delta in two species-number glyphs and return to HOME proves
DS-mode input/navigation in this development ROM, not original 3DS parity,
DSi hardware/camera operation, source geometry, or physical keypad behavior.
"""
import sys
from pathlib import Path
import struct
from c253_melonds_frame_gate import inspect


def frame(path):
    data = Path(path).read_bytes()
    info = inspect(path)
    header = struct.unpack_from('>25I', data)
    start = header[0] + header[19] * 12
    return info['width'], info['height'], header[12], header[11] // 8, memoryview(data)[start:start + header[12] * header[5]]


def verify_navigation(home, dex, right, back):
    frames = [frame(p) for p in (home, dex, right, back)]
    shape = frames[0][:4]
    if any(f[:4] != shape for f in frames):
        raise ValueError('melonDS capture geometry changed')
    width, height, row, pixel = shape
    # The verified melonDS 1.1 capture has a 19px Qt menu above 2x192px.
    # Reject other layouts instead of confusing GUI chrome with DS pixels.
    if (width, height) != (256, 403):
        raise ValueError('unrecognized melonDS 1.1 256x403 DS capture')

    def delta(i, j, box, step=1):
        a, b = frames[i][4], frames[j][4]
        x0, y0, x1, y1 = box
        return sum(a[y * row + x * pixel:y * row + x * pixel + 3] !=
                   b[y * row + x * pixel:y * row + x * pixel + 3]
                   for y in range(y0, y1, step) for x in range(x0, x1, step))

    # Exact source-asset-free C253 screenshot number-glyph locations.
    top_number = delta(1, 2, (117, 56, 146, 71))
    bottom_number = delta(1, 2, (68, 311, 100, 331))
    opened = delta(0, 1, (0, 42, 256, 185), 2) + delta(0, 1, (0, 270, 256, 391), 2)
    restored = delta(0, 3, (0, 42, 256, 185), 2) + delta(0, 3, (0, 270, 256, 391), 2)
    result = {'home_to_dex_samples': opened,
              'right_top_number_pixels': top_number,
              'right_bottom_number_pixels': bottom_number,
              'after_b_home_delta_samples': restored,
              'original_asset_fidelity_verified': False,
              'dsi_camera_verified': False}
    if opened < 100:
        raise ValueError(f'Pokédex was not visibly open: {result}')
    if top_number < 6 or bottom_number < 6:
        raise ValueError(f'Right did not change BOTH Pokédex number glyphs: {result}')
    if restored > max(25, opened // 8):
        raise ValueError(f'B did not restore HOME: {result}')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit('usage: c254_melonds_nav_gate.py HOME.xwd DEX.xwd RIGHT.xwd BACK.xwd')
    print('C254 real melonDS DS-mode Right/B evidence:', verify_navigation(*sys.argv[1:]))
