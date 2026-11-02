#!/usr/bin/env python3
"""C242: asset-free DeSmuME XWD→PNG evidence with ROM/source SHA provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

from c235_emulator_frame_gate import read_xwd

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
MAX_ROM_BYTES = 4 * 1024 * 1024


def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))


def xwd_to_png(path):
    data = Path(path).read_bytes()
    shape, pixels = read_xwd(path)
    width, height, row_bytes, pixel_bytes = shape
    h = struct.unpack_from('>25I', data)
    if ((width, height) != (256, 384) or h[7] != 0 or pixel_bytes != 4
            or tuple(h[14:17]) != (0xff0000, 0x00ff00, 0x0000ff)):
        raise ValueError('unsupported XWD layout or channel masks')
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        row = pixels[y * row_bytes:y * row_bytes + width * 4]
        for x in range(0, len(row), 4):
            rows.extend((row[x + 2], row[x + 1], row[x]))
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return (PNG_SIGNATURE + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(bytes(rows), level=9))
            + chunk(b'IEND', b''))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_evidence(rom, commit, frames, output):
    rom = Path(rom)
    output = Path(output)
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('source commit must be a full lowercase SHA-1')
    if not rom.is_file() or rom.is_symlink() or not 512 <= rom.stat().st_size <= MAX_ROM_BYTES:
        raise ValueError('refusing non-asset-free-sized ROM or unsafe path')
    if output.exists() or output.is_symlink():
        raise FileExistsError('evidence output must not already exist')
    if not 1 <= len(frames) <= 8:
        raise ValueError('invalid evidence frame count')
    output.mkdir(mode=0o700)
    result = {'source_commit': commit, 'asset_free_only': True,
              'rom_name': rom.name, 'rom_size': rom.stat().st_size,
              'rom_sha256': sha256(rom), 'frames': []}
    names = set()
    for raw in frames:
        raw = Path(raw)
        if raw.is_symlink() or raw.suffix != '.xwd' or not raw.is_file():
            raise ValueError('unsafe or unsupported frame')
        if raw.name in names:
            raise ValueError('duplicate frame name')
        names.add(raw.name)
        png_path = output / (raw.stem + '.png')
        png_path.write_bytes(xwd_to_png(raw))
        result['frames'].append({'xwd': raw.name, 'xwd_sha256': sha256(raw),
                                 'png': png_path.name, 'png_sha256': sha256(png_path)})
    (output / 'manifest.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('frames', nargs='+', type=Path)
    args = parser.parse_args()
    result = write_evidence(args.rom, args.commit, args.frames, args.output)
    print('C242 asset-free ROM SHA-256:', result['rom_sha256'])
    print('C242 source commit:', result['source_commit'])
    print('C242 PNG/XWD pairs:', len(result['frames']))


if __name__ == '__main__':
    main()
