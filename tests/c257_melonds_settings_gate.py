#!/usr/bin/env python3
"""C257: verify real asset-free melonDS Settings entry, toggle and B exit.

This is DS-mode visual evidence only. It does not establish FAT persistence,
original 3DS artwork, DSi camera behavior, or hardware compatibility.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_settings(scrolled_home, settings, toggled, back):
    frames = [frame(p) for p in (scrolled_home, settings, toggled, back)]
    shape = frames[0][:4]
    if shape[:2] != (256, 403) or any(f[:4] != shape for f in frames):
        raise ValueError('unexpected melonDS dual-screen capture geometry')
    width, height, row, pixel = shape

    def delta(i, j, box, step=2):
        x0, y0, x1, y1 = box
        a, b = frames[i][4], frames[j][4]
        return sum(a[y*row+x*pixel:y*row+x*pixel+3] !=
                   b[y*row+x*pixel:y*row+x*pixel+3]
                   for y in range(y0, y1, step)
                   for x in range(x0, x1, step))

    top = (0, 43, 250, 185)
    labels = (20, 294, 205, 386)
    setting_value = (90, 311, 175, 331)
    unchanged_header = (20, 224, 205, 282)
    opened_top = delta(0, 1, top)
    opened_lower = delta(0, 1, labels)
    toggle_value = delta(1, 2, setting_value, 1)
    toggle_header = delta(1, 2, unchanged_header)
    returned_labels = delta(0, 3, labels)
    result = {
        'settings_top_delta': opened_top,
        'settings_lower_delta': opened_lower,
        'rotation_value_changed_pixels': toggle_value,
        'unchanged_settings_header_delta': toggle_header,
        'after_b_scrolled_home_label_delta': returned_labels,
        'save_persistence_verified': False,
        'dsi_camera_verified': False,
        'original_assets_verified': False,
    }
    if opened_top < 100 or opened_lower < 100:
        raise ValueError(f'Settings did not open on both screens: {result}')
    if toggle_value < 8 or toggle_header > 20:
        raise ValueError(f'Settings rotation toggle not independently visible: {result}')
    if returned_labels > 20:
        raise ValueError(f'Settings B did not restore scrolled HOME: {result}')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit('usage: c257_melonds_settings_gate.py HOME_SCROLLED SETTINGS TOGGLED BACK')
    print('C257 real melonDS Settings evidence:', verify_settings(*sys.argv[1:]))
