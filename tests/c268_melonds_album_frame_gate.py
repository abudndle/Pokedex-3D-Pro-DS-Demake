#!/usr/bin/env python3
"""C268: strict synthetic-photo Album UI transitions in real melonDS XWD frames.

Pixel evidence alone is not a text/OCR or original asset authenticity check.
The independent FAT roster gate must also verify deletion on disk.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_album(home, first, second, returned, confirm, deleted, resumed):
    frames = [frame(p) for p in (home, first, second, returned, confirm, deleted, resumed)]
    shape = frames[0][:4]
    if shape[:2] != (256, 403) or any(f[:4] != shape for f in frames):
        raise ValueError('melonDS Album capture geometry mismatch')
    _, _, row, stride = shape

    def delta(a, b, box, step=2):
        x0, y0, x1, y1 = box
        left, right = frames[a][4], frames[b][4]
        return sum(left[y*row+x*stride:y*row+x*stride+3] !=
                   right[y*row+x*stride:y*row+x*stride+3]
                   for y in range(y0, y1, step)
                   for x in range(x0, x1, step))

    top = (0, 45, 250, 188)
    lower = (0, 291, 245, 380)
    labels = (0, 304, 240, 374)
    result = {
        'opened_top': delta(0, 1, top),
        'opened_lower': delta(0, 1, lower),
        'page_right_top': delta(1, 2, top),
        'page_right_lower': delta(1, 2, labels),
        'page_left_restored': delta(1, 3, labels),
        'delete_prompt_top': delta(3, 4, top),
        'deleted_top': delta(4, 5, top),
        'deleted_lower': delta(4, 5, labels),
        'reboot_restored_lower': delta(5, 6, labels),
        'original_asset_fidelity_verified': False,
        'dsi_camera_verified': False,
    }
    if result['opened_top'] < 100 or result['opened_lower'] < 100:
        raise ValueError(f'Album did not open on both screens: {result}')
    if result['page_right_top'] < 10 or result['page_right_lower'] < 10:
        raise ValueError(f'Album Right did not change both filename lists: {result}')
    if result['page_left_restored'] > 20:
        raise ValueError(f'Album Left did not restore first page: {result}')
    if result['delete_prompt_top'] < 8:
        raise ValueError(f'Album X did not display delete confirmation: {result}')
    if result['deleted_top'] < 8 or result['deleted_lower'] < 8:
        raise ValueError(f'Album A did not change photo list on both screens: {result}')
    if result['reboot_restored_lower'] > 20:
        raise ValueError(f'Album did not persist deleted photo list across boot: {result}')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 8:
        raise SystemExit('usage: c268_melonds_album_frame_gate.py HOME FIRST SECOND RETURN CONFIRM DELETED RESUMED')
    print('C268 real melonDS Album frame transitions:', verify_album(*sys.argv[1:]))
