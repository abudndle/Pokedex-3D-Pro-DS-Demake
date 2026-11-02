#!/usr/bin/env python3
"""C256: real asset-free melonDS DS Challenge/Records/Album/B frame gate.

Only development-menu navigation is accepted, not saved progress, authentic
3DS content, original assets, DSi camera or hardware compatibility.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_pages(home, *pages_and_returns):
    if len(pages_and_returns) != 6:
        raise ValueError('expected three menu page/return frame pairs')
    frames = [frame(p) for p in (home, *pages_and_returns)]
    shape = frames[0][:4]
    if any(f[:4] != shape for f in frames):
        raise ValueError('melonDS frame geometry changed')
    width, height, row, pixel = shape
    if (width, height) != (256, 403):
        raise ValueError('unrecognized melonDS 1.1 DS-mode window')
    def delta(i, j, box):
        a, b = frames[i][4], frames[j][4]
        x0, y0, x1, y1 = box
        return sum(a[y*row+x*pixel:y*row+x*pixel+3] !=
                   b[y*row+x*pixel:y*row+x*pixel+3]
                   for y in range(y0, y1, 2) for x in range(x0, x1, 2))
    top = (0, 43, 250, 185)
    menu = (20, 294, 205, 386)
    results = {}
    for index, name in enumerate(('challenge', 'records', 'album')):
        page, back = 1 + 2*index, 2 + 2*index
        upper = delta(0, page, top)
        lower = delta(0, page, menu)
        restored = delta(0, back, menu)
        results[name] = {'upper_page_delta': upper,
                         'lower_page_delta': lower,
                         'after_b_home_label_delta': restored}
        if upper < 100 or lower < 100:
            raise ValueError(f'{name} did not visibly open on both screens: {results[name]}')
        if restored > 20:
            raise ValueError(f'{name} B did not restore HOME: {results[name]}')
    results['original_asset_fidelity_verified'] = False
    results['save_persistence_verified'] = False
    results['dsi_camera_verified'] = False
    return results


if __name__ == '__main__':
    if len(sys.argv) != 8:
        raise SystemExit('usage: c256_melonds_menu_gate.py HOME CHALLENGE C_BACK RECORDS R_BACK ALBUM A_BACK')
    print('C256 real melonDS asset-free menu evidence:', verify_pages(*sys.argv[1:]))
