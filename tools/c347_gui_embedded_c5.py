#!/usr/bin/env python3
"""C347: recover bounded 3DS GUI embedded C5 resource metadata privately.

The embedded C5 blocks are original-derived game data, NOT decoded pixels,
and are never to be committed to the public repository.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import zipfile

ROOT_MAGIC = b'\xc5\x78\x00\x01'
INNER_MAGIC = b'\xc5\x78\x00\x02'
EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))
MAX_CONTAINER = 12 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_container(data: bytes):
    if len(data) < 0x78 or len(data) > MAX_CONTAINER or data[:4] != ROOT_MAGIC:
        raise ValueError('invalid outer GUI C5 header')
    # Source-observed field at 0x68 points to an embedded C5 v2 block.
    offset = struct.unpack_from('<I', data, 0x68)[0]
    if offset < 0x78 or offset + 8 > len(data) or data[offset:offset + 4] != INNER_MAGIC:
        raise ValueError('no valid bounded nested C5 header')
    size = struct.unpack_from('<I', data, offset + 4)[0]
    if size < 0x78 or offset + size > len(data):
        raise ValueError('nested C5 length invalid')
    return offset, data[offset:offset + size]


def extract(archive: Path, output_dir: Path):
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError('private output exists')
    if not output_dir.parent.is_dir():
        raise ValueError('private output parent absent')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate ZIP members')
        rows, extracted = [], []
        for base in EXPECTED:
            member = f'decoded_c5/gui/{base}.c5'
            if member not in names:
                raise ValueError('missing source C5 ' + member)
            info = z.getinfo(member)
            if not 0 < info.file_size <= MAX_CONTAINER:
                raise ValueError('source C5 too large')
            data = z.read(member)
            offset, body = read_container(data)
            output = f'{base}.embedded.c5'
            extracted.append((output, body))
            rows.append({'source': member, 'source_sha256': sha(data),
                         'nested_offset': offset, 'nested_length': len(body),
                         'nested_sha256': sha(body), 'private_output': output})
    with tempfile.TemporaryDirectory(prefix='.c347-', dir=output_dir.parent) as tmp:
        stage = Path(tmp)
        for name, data in extracted:
            p = stage / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            if p.read_bytes() != data:
                raise ValueError('private output verification failure')
        report = {'schema': 'c347-embedded-gui-c5-extraction-v1',
                  'archive_sha256': sha(archive.read_bytes()),
                  'nested_source_count': len(rows), 'items': rows,
                  'original_texture_pixels_decoded': False,
                  'original_dual_screen_bitmaps_complete': False,
                  'original_release_ready': False}
        (stage / 'C347_PRIVATE_EXTRACTION.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')
        os.rename(stage, output_dir)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = extract(args.archive, args.output)
    print(json.dumps({'nested_source_count': result['nested_source_count'],
                      'original_release_ready': False}, indent=2))
