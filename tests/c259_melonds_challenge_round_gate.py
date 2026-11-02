#!/usr/bin/env python3
"""C259: real asset-free melonDS Challenge picker/question/review/continue/B.

Visual state transitions do not prove correct scoring, saved records, original
3DS challenge content, hardware or DSi features.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_challenge_round(home, picker, question, review, continued, back):
    frames = [frame(p) for p in (home, picker, question, review, continued, back)]
    shape = frames[0][:4]
    if shape[:2] != (256, 403) or any(f[:4] != shape for f in frames):
        raise ValueError('melonDS Challenge capture geometry mismatch')
    _, _, row, stride = shape

    def delta(i, j, box, step=2):
        x0, y0, x1, y1 = box
        a, b = frames[i][4], frames[j][4]
        return sum(a[y*row+x*stride:y*row+x*stride+3] !=
                   b[y*row+x*stride:y*row+x*stride+3]
                   for y in range(y0, y1, step) for x in range(x0, x1, step))

    top = (0, 44, 250, 185)
    bottom = (0, 278, 245, 385)
    labels = (20, 294, 205, 386)
    states = [('picker', 0, 1), ('question', 1, 2),
              ('review', 2, 3), ('continued', 3, 4)]
    result = {}
    for name, before, after in states:
        result[name + '_top_delta'] = delta(before, after, top)
        result[name + '_bottom_delta'] = delta(before, after, bottom)
        if result[name + '_top_delta'] < 30 or result[name + '_bottom_delta'] < 30:
            raise ValueError(f'Challenge {name} transition not visible on both screens: {result}')
    result['after_b_home_label_delta'] = delta(0, 5, labels)
    result['scoring_correctness_verified'] = False
    result['save_persistence_verified'] = False
    result['original_assets_verified'] = False
    if result['after_b_home_label_delta'] > 20:
        raise ValueError(f'Challenge B did not restore HOME: {result}')
    return result


if __name__ == '__main__':
    if len(sys.argv) != 7:
        raise SystemExit('usage: c259_melonds_challenge_round_gate.py HOME PICKER QUESTION REVIEW CONTINUED BACK')
    print('C259 real melonDS Challenge round:', verify_challenge_round(*sys.argv[1:]))
