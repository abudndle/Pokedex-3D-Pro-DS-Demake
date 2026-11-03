#!/usr/bin/env python3
"""C332: verify same lower-screen Challenge question across real melonDS restart.

Only proves visual continuity in the asset-free DS development ROM; it does
not prove original 3DS artwork, exact private asset text or DSi hardware.
"""
import sys
from c254_melonds_nav_gate import frame


def verify_same_question(before, restored):
    a, b = frame(before), frame(restored)
    if a[:4] != b[:4]:
        raise ValueError('C332 restored frame geometry changed')
    width, height, row, stride = a[:4]
    if (width, height) != (256, 403):
        raise ValueError('C332 expected melonDS 1.1 DS-mode 256x403 capture')
    original, new = a[4], b[4]
    changed = sum(
        original[y*row+x*stride:y*row+x*stride+3] !=
        new[y*row+x*stride:y*row+x*stride+3]
        for y in range(265, 391, 2)
        for x in range(15, 240, 2)
    )
    # Species number, selected option, four source-backed answers and stage
    # must remain visually stable. Ignore upper-screen save/clock differences.
    if changed > 15:
        raise ValueError(f'C332 lower DS Challenge question changed across reboot: {changed} samples')
    return {'lower_changed_samples': changed,
            'asset_free_second_question_continuity': True,
            'original_3ds_asset_fidelity_verified': False,
            'dsi_hardware_verified': False}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: c332_melonds_resume_frame_gate.py BEFORE.xwd AFTER.xwd')
    print('C332 genuine melonDS third-boot question continuity:',
          verify_same_question(sys.argv[1], sys.argv[2]))
