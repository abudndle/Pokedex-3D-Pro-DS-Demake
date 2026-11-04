#!/usr/bin/env python3
"""C348 private-ROM DeSmuME frame evidence (run only in a PRIVATE repository).

The development ROM may contain original licensed assets. This verifier must
not be invoked in public CI using such a ROM, nor may screenshots be uploaded
to a public repository. It proves that both emulated displays drew nonblank
frames, not original visual fidelity, source-asset usage or game parity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from c235_emulator_frame_gate import read_xwd
from c242_emulator_evidence import xwd_to_png

MAX_ROM_BYTES = 512 * 1024 * 1024
MAX_SCREEN_XWD_BYTES = 2 * 1024 * 1024


def file_hash(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def inspect_frame(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 100 <= path.stat().st_size <= MAX_SCREEN_XWD_BYTES:
        raise ValueError('unsafe or oversized emulator frame')
    shape, pixels = read_xwd(path)
    width, height, row_bytes, stride = shape
    if (width, height, stride) != (256, 384, 4):
        raise ValueError('expected native 256x384 two-screen XWD frame')
    per_screen = []
    for begin, end in ((0, 192), (192, 384)):
        count = 0
        light = 0
        distinct = set()
        for y in range(begin, end, 4):
            for x in range(0, width, 4):
                p = y * row_bytes + x * stride
                rgb = bytes(pixels[p:p + 3])
                distinct.add(rgb)
                light += max(rgb) > 16
                count += 1
        per_screen.append({'sampled_pixels': count, 'nonblack_ratio': round(light / count, 5),
                           'unique_sampled_colors': len(distinct)})
    if any(s['unique_sampled_colors'] < 2 or s['nonblack_ratio'] < .01 for s in per_screen):
        raise ValueError(f'blank/unpainted DS screen(s): {per_screen}')
    return per_screen


def evidence(rom, frames, out):
    rom, out = Path(rom), Path(out)
    if rom.is_symlink() or not rom.is_file() or not 512 <= rom.stat().st_size <= MAX_ROM_BYTES:
        raise ValueError('invalid private DS ROM input')
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        raise ValueError('output must be an absent private directory')
    if not 1 <= len(frames) <= 4:
        raise ValueError('expected 1..4 emulator frames')
    found = []
    for frame in frames:
        frame = Path(frame)
        if frame.suffix != '.xwd' or not re.fullmatch(r'[a-z][a-z0-9_-]{0,40}', frame.stem):
            raise ValueError('unsafe XWD frame name')
        screens = inspect_frame(frame)
        png = xwd_to_png(frame)  # Fail closed on unsupported XWD pixel mask/orientation.
        found.append((frame, screens, png))
    out.mkdir(mode=0o700)
    try:
        records = []
        for frame, screens, png in found:
            target = out / (frame.stem + '.png')
            target.write_bytes(png)
            records.append({'frame': frame.name, 'frame_sha256': file_hash(frame),
                            'png': target.name, 'png_sha256': file_hash(target),
                            'screens': screens})
        result = {
            'schema': 'c348-private-rom-emulator-visual-evidence-v1',
            'rom_bytes': rom.stat().st_size, 'rom_sha256': file_hash(rom),
            'frames': records,
            'both_ds_screens_nonblank': True,
            'asset_integrated_emulator_started': True,
            'original_3ds_screen_parity_verified': False,
            'native_model_texture_animation_appearance_verified': False,
            'full_gameplay_verified': False,
            'release_ready': False,
        }
        (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    except BaseException:
        for path in out.iterdir():
            path.unlink()
        out.rmdir()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('frames', nargs='+', type=Path)
    args = parser.parse_args()
    result = evidence(args.rom, args.frames, args.output)
    print('C348 emulator drew both private-ROM DS screens; original visual parity UNVERIFIED')
    print('Private ROM SHA-256:', result['rom_sha256'])


if __name__ == '__main__':
    main()
