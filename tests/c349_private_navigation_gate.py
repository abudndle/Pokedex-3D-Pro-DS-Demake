#!/usr/bin/env python3
"""C349: verify real private asset-integrated ROM menu input with XWD evidence.

Requires captured HOME, A-opened Dex, Right-browsed Dex and B-returned HOME.
Checks only observable lower-screen changes; cannot establish authentic 3DS art.
Never place original-derived PNGs or ROMs in a public GitHub artifact.
"""
import argparse
import hashlib
import json
from pathlib import Path

from c235_emulator_frame_gate import read_xwd


def bottom_changed(first, second, step=2):
    (shape_a, pixels_a), (shape_b, pixels_b) = read_xwd(first), read_xwd(second)
    if shape_a != shape_b or shape_a[:2] != (256, 384) or shape_a[3] != 4:
        raise ValueError('C349 requires matching native 256x384 32bpp windows')
    width, _, row_bytes, stride = shape_a
    return sum(
        pixels_a[y * row_bytes + x * stride:y * row_bytes + x * stride + 3] !=
        pixels_b[y * row_bytes + x * stride:y * row_bytes + x * stride + 3]
        for y in range(192, 384, step) for x in range(0, width, step)
    )


def full_changed(first, second, step=2):
    (shape_a, pixels_a), (shape_b, pixels_b) = read_xwd(first), read_xwd(second)
    if shape_a != shape_b or shape_a[:2] != (256, 384) or shape_a[3] != 4:
        raise ValueError('C349 requires matching native 256x384 32bpp windows')
    width, height, row_bytes, stride = shape_a
    return sum(
        pixels_a[y * row_bytes + x * stride:y * row_bytes + x * stride + 3] !=
        pixels_b[y * row_bytes + x * stride:y * row_bytes + x * stride + 3]
        for y in range(0, height, step) for x in range(0, width, step)
    )


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify(home, dex, next_dex, back, output):
    """Fail closed on no input response or failure to return to HOME."""
    home, dex, next_dex, back, output = map(Path, (home, dex, next_dex, back, output))
    if output.exists() or not output.parent.is_dir():
        raise ValueError('verification report destination must not exist')
    opened = bottom_changed(home, dex)
    browsed_lower = bottom_changed(dex, next_dex, step=1)
    browsed_all = full_changed(dex, next_dex, step=1)
    restored = bottom_changed(home, back)
    result = {
        'schema': 'c349-private-rom-navigation-evidence-v1',
        'private_asset_integrated_rom_navigation': False,
        'home_to_dex_changed_lower_sample_pixels': opened,
        'right_browse_changed_lower_pixels': browsed_lower,
        'right_browse_changed_both_screen_pixels': browsed_all,
        'back_to_home_changed_lower_sample_pixels': restored,
        'frames_sha256': {
            path.stem: sha256(path)
            for path in (home, dex, next_dex, back)
        },
        'original_gui_parity_verified': False,
        'original_model_animation_verified': False,
        'full_gameplay_verified': False,
        'release_ready': False,
    }
    if opened < 100:
        raise ValueError(f'HOME A did not visibly open Dex: {result}')
    if browsed_all < 10:
        raise ValueError(f'Dex Right did not visibly change the screen: {result}')
    if restored > max(35, opened // 8):
        raise ValueError(f'B did not visibly restore HOME: {result}')
    result['private_asset_integrated_rom_navigation'] = True
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('home', 'dex', 'next_dex', 'back'):
        p.add_argument(name, type=Path)
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(verify(a.home, a.dex, a.next_dex, a.back, a.report), indent=2))
