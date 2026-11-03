#!/usr/bin/env python3
"""C333 independent FAT verifier for exact reopened Pokédex details."""
import argparse
from pathlib import Path
import struct
from c260_fat_slot_gate import valid_slots, valid_resume_slots


def check(root: Path):
    progress = valid_slots(root,'pokedex3d',b'P3SV',64,60)
    resume = valid_resume_slots(root)
    if progress[16] != 1 or struct.unpack_from('<H', progress,20)[0] != 0:
        raise ValueError('previous favorite missing')
    if resume[4] != 5 or resume[76] != 1 or resume[12] != 0 or resume[13] != 1:
        raise ValueError('C333 exact live detail tab v5 not present')
    species = struct.unpack_from('<H',resume,16)[0]
    form = struct.unpack_from('<H',resume,24)[0]
    if species != 0 or form != 0:
        raise ValueError('C333 resumed incorrect species/form')
    return {'p3rv_version':5,'detail_tab':1,'species':species,
            'form':form,'prior_favorite_preserved':True}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('root',type=Path)
    print('C333 real FAT species detail checkpoint:',check(p.parse_args().root))
