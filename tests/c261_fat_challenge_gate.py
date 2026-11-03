#!/usr/bin/env python3
"""C261/C332: verify real FAT Challenge totals and exact v4 active checkpoint."""
import argparse
from pathlib import Path
import struct
from c260_fat_slot_gate import valid_slots, valid_resume_slots


def check(root: Path, require_active=False):
    save = valid_slots(root, 'pokedex3d', b'P3SV', 64, 60)
    resume = valid_resume_slots(root)
    correct, total = struct.unpack_from('<II', save, 32)
    if not 1 <= total <= 100000000 or correct > total:
        raise ValueError('Challenge answer count missing or invalid')
    if save[16] != 1 or struct.unpack_from('<H', save, 20)[0] != 0:
        raise ValueError('favorite lost during Challenge progress')
    if resume[12] != 0 or resume[13] != 6:
        raise ValueError('Challenge page checkpoint missing')
    active = resume[4] == 4
    if require_active and not active:
        raise ValueError('C332 exact active P3RV v4 checkpoint missing')
    if active:
        # The C260 sequence: enter mode 0, answer Q1, advance to Q2,
        # then shut down. Reboot must not manufacture a fresh question.
        if resume[76] != 1 or resume[77] != 1 or resume[78] != 0 or resume[79] != 1:
            raise ValueError('C332 expected active second question checkpoint')
        chosen, answer = resume[81], resume[82]
        pokemon = struct.unpack_from('<H', resume, 84)[0]
        choices = struct.unpack_from('<4H', resume, 86)
        asked = struct.unpack_from('<10H', resume, 94)
        seed = struct.unpack_from('<I', resume, 114)[0]
        ck_answers, ck_correct, ck_rounds = struct.unpack_from('<III', resume, 118)
        if chosen > 3 or answer > 3 or seed == 0 or            not (493 <= pokemon <= 648) or pokemon != choices[answer] or            len(set(choices)) != 4 or any(not 493 <= p <= 648 for p in choices) or            asked[1] != pokemon or not 493 <= asked[0] <= 648 or            asked[0] == asked[1] or any(asked[2:]) or            ck_answers < total or ck_correct < correct or ck_correct > ck_answers or            ck_rounds != 0:
            raise ValueError('C332 invalid or stale active question identity')
    elif resume[4] != 3:
        raise ValueError('unknown Challenge checkpoint version')
    return {'challenge_answers': total, 'correct': correct,
            'favorite_000': True, 'challenge_page_checkpoint': True,
            'active_second_question_v4': active}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('export_root', type=Path)
    p.add_argument('--require-active', action='store_true')
    args = p.parse_args()
    print('C261/C332 FAT Challenge gate:', check(args.export_root, args.require_active))
