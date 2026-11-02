#!/usr/bin/env python3
"""C243: asset-free DeSmuME touchscreen Move Dex and disabled-AR frame gate.

Proves observable native development-menu transitions only. It does not prove
original 3DS art, private models, physical hardware, or camera availability.
"""
import argparse
from pathlib import Path
from c235_emulator_frame_gate import read_xwd

BOTTOM = (0, 192, 256, 384)


def bottom_changed(a, b, step=2):
    (shape_a, pixels_a), (shape_b, pixels_b) = read_xwd(a), read_xwd(b)
    if shape_a != shape_b or shape_a[:2] != (256, 384):
        raise ValueError('expected matching 256x384 dual-screen frames')
    width, _, stride, bpp = shape_a
    x0, y0, x1, y1 = BOTTOM
    return sum(pixels_a[y * stride + x * bpp:y * stride + x * bpp + 3] !=
               pixels_b[y * stride + x * bpp:y * stride + x * bpp + 3]
               for y in range(y0, y1, step) for x in range(x0, x1, step))


def verify(home, move, back, ar_selected, ar_after_a):
    # Only bottom-screen pixels are compared: the diagnostic ARM9 frame
    # counter is intentionally excluded from the acceptance region.
    opened = bottom_changed(home, move)
    restored = bottom_changed(home, back)
    highlighted = bottom_changed(back, ar_selected)
    denied = bottom_changed(ar_selected, ar_after_a)
    result = {'home_to_move_dex_lower_pixels': opened,
              'move_dex_b_to_home_lower_pixels': restored,
              'ar_selection_lower_pixels': highlighted,
              'ar_a_denied_lower_pixels': denied}
    if opened < 100:
        raise ValueError(f'Move Dex touch did not open a visible page: {result}')
    if restored > 10:
        raise ValueError(f'B did not restore lower HOME: {result}')
    if highlighted < 10:
        raise ValueError(f'AR Viewer touch did not select a distinct HOME entry: {result}')
    if denied > 10:
        raise ValueError(f'DS-only AR Viewer A entered or changed page: {result}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('home', 'move', 'back', 'ar_selected', 'ar_after_a'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    print('C243 verified asset-free DeSmuME touch navigation:',
          verify(args.home, args.move, args.back, args.ar_selected,
                 args.ar_after_a))


if __name__ == '__main__':
    main()
