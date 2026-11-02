#!/usr/bin/env python3
"""C262: reject unchanged Challenge phases in real asset-free melonDS XWD.

This verifies only visible DS-mode phase transitions. The C261 FAT gate
separately verifies actual score and resume persistence; neither gate proves
original 3DS graphics, content, DSi camera or hardware.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_phases(question, review, continued):
    frames = [frame(path) for path in (question, review, continued)]
    shape = frames[0][:4]
    if any(item[:4] != shape for item in frames):
        raise ValueError('Challenge capture geometry changed')
    width, height, row, stride = shape
    if (width, height) != (256, 403):
        raise ValueError('unrecognized melonDS 1.1 DS-mode capture')

    def difference(a, b, y0, y1):
        x0, x1 = 15, 240
        pixels_a, pixels_b = frames[a][4], frames[b][4]
        return sum(
            pixels_a[y*row+x*stride:y*row+x*stride+3] !=
            pixels_b[y*row+x*stride:y*row+x*stride+3]
            for y in range(y0, y1, 2)
            for x in range(x0, x1, 2)
        )

    result = {}
    for a, b, name in ((0, 1, 'question_to_review'),
                       (1, 2, 'review_to_continue'),
                       (0, 2, 'question_to_continue')):
        top = difference(a, b, 43, 189)
        bottom = difference(a, b, 265, 391)
        result[name] = {'upper_samples': top, 'lower_samples': bottom}
        # Exclude Qt chrome and top-only animation: Challenge choices and
        # answer feedback must visibly change on the touchscreen itself.
        if bottom < 12:
            raise ValueError(f'{name} did not change lower DS Challenge UI: {result[name]}')
    result['real_gameplay_scoring_verified'] = False
    result['original_assets_verified'] = False
    result['dsi_camera_verified'] = False
    return result


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('usage: c262_melonds_challenge_phase_gate.py QUESTION REVIEW CONTINUED')
    print('C262 asset-free Challenge phase transitions:', verify_phases(*sys.argv[1:]))
