#!/usr/bin/env python3
"""C261: verify real FAT challenge counters and Challenge page checkpoint."""
import argparse
from pathlib import Path
import struct
from c260_fat_slot_gate import valid_slots


def check(root: Path):
    save = valid_slots(root, 'pokedex3d', b'P3SV', 64, 60)
    resume = valid_slots(root, 'pokedex3d_resume', b'P3RV', 80, 76)
    correct, total = struct.unpack_from('<II', save, 32)
    if not 1 <= total <= 100000000 or correct > total:
        raise ValueError('Challenge answer count missing or invalid')
    if save[16] != 1 or struct.unpack_from('<H', save, 20)[0] != 0:
        raise ValueError('favorite lost during Challenge progress')
    if resume[4] != 3 or resume[12] != 0 or resume[13] != 6:
        raise ValueError('Challenge page checkpoint missing')
    return {'challenge_answers': total, 'correct': correct,
            'favorite_000': True, 'challenge_page_checkpoint': True}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('export_root', type=Path)
    print('C261 FAT Challenge gate:', check(p.parse_args().export_root))
