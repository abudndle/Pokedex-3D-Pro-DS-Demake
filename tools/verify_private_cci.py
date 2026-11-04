#!/usr/bin/env python3
"""Read-only Nintendo 3DS NCSD/NCCH envelope validation for privately held dumps."""
import argparse
import json
import struct
from pathlib import Path
SECTOR = 512

def validate(path):
    size = path.stat().st_size
    with path.open('rb') as f:
        header = f.read(SECTOR)
        if len(header) != SECTOR or header[0x100:0x104] != b'NCSD':
            raise ValueError('not an NCSD header')
        capacity = struct.unpack_from('<I', header, 0x104)[0] * SECTOR
        partitions = []
        previous_end = 0
        for index in range(8):
            start, sectors = struct.unpack_from('<II', header, 0x120 + index * 8)
            if start == sectors == 0:
                continue
            if not start or not sectors:
                raise ValueError(f'partition {index}: half-empty table entry')
            offset = start * SECTOR
            length = sectors * SECTOR
            end = offset + length
            if offset < SECTOR or end > size or offset < previous_end:
                raise ValueError(f'partition {index}: invalid/overlapping range')
            f.seek(offset + 0x100)
            if f.read(4) != b'NCCH':
                raise ValueError(f'partition {index}: missing NCCH magic')
            partitions.append({'index': index, 'offset_bytes': offset,
                               'length_bytes': length, 'end_bytes': end, 'format': 'NCCH'})
            previous_end = end
        if not partitions:
            raise ValueError('empty partition table')
        return {'format': 'NCSD', 'file_bytes': size,
                'advertised_capacity_bytes': capacity,
                'capacity_exceeds_file': capacity > size,
                'partitions': partitions, 'validation': 'PASS'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('cci', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        result = validate(args.cci)
    except (OSError, ValueError) as error:
        p.exit(1, f'CCI validation FAILED: {error}\n')
    content = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content, end='')

if __name__ == '__main__':
    main()
