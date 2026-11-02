#!/usr/bin/env python3
"""C258: verify real melonDS DS Records Right-tab changes and B return.

The test does not prove persistence, original assets or DSi features.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_records_tabs(home, regions, recent, quizzes, back):
    frames = [frame(p) for p in (home, regions, recent, quizzes, back)]
    shape = frames[0][:4]
    if shape[:2] != (256, 403) or any(f[:4] != shape for f in frames):
        raise ValueError('melonDS Records capture geometry mismatch')
    _, _, row, stride = shape

    def changed(a, b, box, step=2):
        x0, y0, x1, y1 = box
        first, second = frames[a][4], frames[b][4]
        return sum(first[y*row+x*stride:y*row+x*stride+3] !=
                   second[y*row+x*stride:y*row+x*stride+3]
                   for y in range(y0, y1, step) for x in range(x0, x1, step))

    top = (0, 44, 250, 185)
    tab_label = (0, 278, 205, 303)
    menu = (20, 294, 205, 386)
    result = {
        'records_open_top_delta': changed(0, 1, top),
        'regions_to_recent_top_delta': changed(1, 2, top),
        'regions_to_recent_label_delta': changed(1, 2, tab_label, 1),
        'recent_to_quizzes_top_delta': changed(2, 3, top),
        'recent_to_quizzes_label_delta': changed(2, 3, tab_label, 1),
        'after_b_home_label_delta': changed(0, 4, menu),
        'save_persistence_verified': False,
        'original_assets_verified': False,
        'dsi_camera_verified': False,
    }
    if result['records_open_top_delta'] < 100:
        raise ValueError(f'Records did not open: {result}')
    for name in ('regions_to_recent', 'recent_to_quizzes'):
        if result[name + '_top_delta'] < 30 or result[name + '_label_delta'] < 8:
            raise ValueError(f'Records {name} did not update both screens: {result}')
    if result['after_b_home_label_delta'] > 20:
        raise ValueError(f'Records B did not restore HOME: {result}')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 6:
        raise SystemExit('usage: c258_melonds_records_tabs_gate.py HOME REGIONS RECENT QUIZZES BACK')
    print('C258 real melonDS Records tabs:', verify_records_tabs(*sys.argv[1:]))
