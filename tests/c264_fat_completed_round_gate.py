#!/usr/bin/env python3
"""C264: verify actual full ten-question Challenge round in native FAT files."""
import argparse
from pathlib import Path
import struct
from c260_fat_slot_gate import valid_slots


def check(root: Path):
    save = valid_slots(root, 'pokedex3d', b'P3SV', 64, 60)
    resume = valid_slots(root, 'pokedex3d_resume', b'P3RV', 80, 76)
    records = valid_slots(root, 'pokedex3d_records', b'P3RC', 160, 156)
    correct, total = struct.unpack_from('<II', save, 32)
    if save[4] != 1 or total != 10 or correct > total:
        raise ValueError('full ten-answer Challenge progress missing')
    if save[16] != 1 or struct.unpack_from('<H', save, 20)[0] != 0:
        raise ValueError('favorite #001 lost')
    if resume[4] != 3 or resume[12] != 0 or resume[13] != 6:
        raise ValueError('Challenge resume checkpoint missing')
    if records[4] != 1 or records[16:98] != b'\x01' + bytes(81):
        raise ValueError('Records viewed species invalid')
    if struct.unpack_from('<8H', records, 100) != (0,) + (0xFFFF,) * 7:
        raise ValueError('Records recent #001 missing')
    runs = struct.unpack_from('<7H', records, 116)
    best = records[130:137]
    rounds = struct.unpack_from('<I', records, 140)[0]
    if rounds != 1 or runs != (1, 0, 0, 0, 0, 0, 0):
        raise ValueError('one completed Challenge round not recorded')
    if best[0] != correct or best[1:] != bytes([0xFF]) * 6:
        raise ValueError('Challenge high score mismatch')
    return {'ten_answers': total, 'correct': correct, 'rounds': rounds,
            'mode0_runs': runs[0], 'best': best[0], 'favorite_001': True,
            'p3sv_p3rv_p3rc_crc': 'valid'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('export_root', type=Path)
    print('C264 completed Challenge round FAT gate:', check(parser.parse_args().export_root))
