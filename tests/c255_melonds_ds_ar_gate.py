#!/usr/bin/env python3
"""C255: independent asset-free melonDS DS-mode AR-disabled + Move Dex gate.

This only proves DS-mode menu behavior in the development ROM. DSi camera,
DSi-mode operation, original 3DS artwork and hardware are NOT verified.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_ds_ar_and_move(home, ar_tap, move, back):
    frames = [frame(p) for p in (home, ar_tap, move, back)]
    shape = frames[0][:4]
    if any(f[:4] != shape for f in frames):
        raise ValueError('melonDS frame shape changed')
    width, height, row, stride = shape
    if (width, height) != (256, 403):
        raise ValueError('unrecognized melonDS DS-mode capture')

    def changed(i, j, box, step=2):
        x0, y0, x1, y1 = box
        a, b = frames[i][4], frames[j][4]
        return sum(a[y*row+x*stride:y*row+x*stride+3] !=
                   b[y*row+x*stride:y*row+x*stride+3]
                   for y in range(y0, y1, step) for x in range(x0, x1, step))

    # Text-menu labels must remain after disabled AR tap. Ignore x<20
    # because the selection arrow may legitimately move to the disabled row.
    labels = (20, 294, 205, 386)
    upper = (0, 43, 250, 185)
    ar_changed = changed(0, 1, labels)
    move_changed = changed(0, 2, labels)
    move_upper = changed(0, 2, upper)
    back_changed = changed(0, 3, labels)
    result = {'disabled_ar_menu_label_delta': ar_changed,
              'move_dex_menu_label_delta': move_changed,
              'move_dex_upper_delta': move_upper,
              'after_b_menu_label_delta': back_changed,
              'dsi_camera_verified': False,
              'original_assets_verified': False}
    if ar_changed > 20:
        raise ValueError(f'AR Viewer unexpectedly replaced DS HOME menu: {result}')
    if move_changed < 100 or move_upper < 100:
        raise ValueError(f'Move Dex did not visibly open on both screens: {result}')
    if back_changed > 20:
        raise ValueError(f'Move Dex B did not restore HOME menu: {result}')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit('usage: c255_melonds_ds_ar_gate.py HOME AR_TAP MOVE BACK')
    print('C255 real melonDS DS-mode AR/Move Dex evidence:', verify_ds_ar_and_move(*sys.argv[1:]))
