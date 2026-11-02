#!/usr/bin/env python3
"""C263: independent native P3RC Records visit persistence on real FAT.

Only validates asset-free DS-mode gameplay state, not original 3DS data.
"""
import argparse
from pathlib import Path
import struct
from c260_fat_slot_gate import valid_slots


def check(root: Path):
    data = valid_slots(root, 'pokedex3d_records', b'P3RC', 160, 156)
    if data[4] != 1:
        raise ValueError('invalid native Records version')
    # The C260/C261 route visits exactly #001 before opening Challenge.
    # No other Pokédex entry should be marked visited by a HOME boot.
    seen = data[16:98]
    if seen != b'\x01' + bytes(81):
        raise ValueError('Records viewed species mismatch')
    recent = struct.unpack_from('<8H', data, 100)
    if recent != (0,) + (0xFFFF,) * 7:
        raise ValueError('Records recent species order mismatch')
    runs = struct.unpack_from('<7H', data, 116)
    best = data[130:137]
    rounds = struct.unpack_from('<I', data, 140)[0]
    if any(runs) or best != bytes([0xFF]) * 7 or rounds:
        raise ValueError('incomplete Challenge incorrectly credited as Records round')
    return {'viewed_001': True, 'recent_001': True,
            'completed_challenge_rounds': 0, 'p3rc_crc': 'valid'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('export_root', type=Path)
    print('C263 FAT Records gate:', check(parser.parse_args().export_root))
