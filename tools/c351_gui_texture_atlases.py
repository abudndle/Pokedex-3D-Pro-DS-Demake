#!/usr/bin/env python3
"""C351 source-exact original 3DS GUI texture descriptor and RGBA8 decoder.

Read owner's private original C5 recovery ZIP. Recover C5 texture names,
GPU byte ranges, native dimensions and source bytes. Decode ONLY confirmed
32-bit ABGR PICA Morton-tiled atlases, write lossless RGBA PNG and quantized
A1RGB5 DS-native atlas candidates in private isolated stage. Other tokens
remain opaque and block any claim of complete original UI conversion.
Never run original assets or derived PNGs in public CI or public artifacts.
"""
from collections import Counter
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
import zipfile
import zlib

C5_MAGIC = b'\xc5\x78\x00\x01'
MAX_C5 = 12 * 1024 * 1024
TEXTURE_ENTRY = struct.Struct('<7I')
RGBA8_TOKEN = 0x14016752
# Source-observed bytes/pixel only, NOT assumed channel semantics for non-RGBA8.
KNOWN_BPP = {0x14016752: 32, 0x14016758: 16, 0x14016757: 8,
             0x14016754: 24, 0x80336752: 16}
EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def descriptors(data):
    """Check the source C5 texture descriptor table and GPU range exactly."""
    if len(data) < 0x100 or len(data) > MAX_C5 or data[:4] != C5_MAGIC:
        raise ValueError('invalid original GUI C5 root')
    meta, gpu_len = struct.unpack_from('<II', data, 4)
    gpu_start = 0x78 + meta
    if gpu_start + gpu_len != len(data) or not gpu_len:
        raise ValueError('inconsistent C5 GPU data length')
    count_word = struct.unpack_from('<I', data, 0x0c)[0]
    if count_word & 0xffff:
        raise ValueError('unsupported C5 texture count flags')
    count = count_word >> 16
    table_start, table_end, names = (struct.unpack_from('<I', data, off)[0]
                                     for off in (0x58, 0x5c, 0x64))
    if (not 1 <= count <= 64 or table_start != 0x78 or
            table_end != table_start + TEXTURE_ENTRY.size * count or
            not table_end <= names < gpu_start):
        raise ValueError('C5 texture descriptor/name table boundary mismatch')
    expected_offset = 0
    rows = []
    seen_names = set()
    for i in range(count):
        offset, reserved, name_ref, nbytes, packed_dim, token, flags = TEXTURE_ENTRY.unpack_from(data, table_start + TEXTURE_ENTRY.size * i)
        width, height = packed_dim & 0xffff, packed_dim >> 16
        if (reserved or flags != 0x10001 or token not in KNOWN_BPP or
                width < 8 or width > 1024 or height < 8 or height > 1024 or
                width & (width - 1) or height & (height - 1) or
                not nbytes or offset != expected_offset or
                nbytes != width * height * KNOWN_BPP[token] // 8):
            raise ValueError(f'invalid source C5 texture descriptor {i}')
        expected_offset += nbytes
        if expected_offset > gpu_len:
            raise ValueError('source C5 texture extends past GPU region')
        start = names + name_ref
        if start < names or start >= gpu_start:
            raise ValueError('source texture name offset outside string region')
        end = data.find(b'\0', start, min(gpu_start, start + 65))
        if end < 0:
            raise ValueError('unterminated original GUI texture name')
        try:
            name = data[start:end].decode('ascii')
        except UnicodeDecodeError as exc:
            raise ValueError('non-ascii original GUI texture name') from exc
        if not re.fullmatch(r'[a-zA-Z0-9_]{1,64}', name) or name in seen_names:
            raise ValueError('unsafe or duplicate original GUI texture name')
        seen_names.add(name)
        payload = data[gpu_start + offset:gpu_start + expected_offset]
        rows.append({'index': i, 'name': name, 'gpu_offset': offset,
                     'gpu_bytes': nbytes, 'width': width, 'height': height,
                     'token': f'{token:08x}', 'bits_per_pixel': KNOWN_BPP[token],
                     'gpu_sha256': sha256(payload),
                     'rgba8_decoder_supported': token == RGBA8_TOKEN})
    if expected_offset != gpu_len:
        raise ValueError('source texture table does not account for all GPU bytes')
    return rows, gpu_start


def decode_morton_abgr8(payload, width, height):
    """Unswizzle 3DS 8x8 Morton ABGR bytes to top-left RGBA8 raster.

    The original PICA tiled texel rows run bottom-up in visible UV space.
    """
    if (width < 8 or height < 8 or width % 8 or height % 8 or
            len(payload) != width * height * 4):
        raise ValueError('invalid native 3DS RGBA8 texture dimensions')
    output = bytearray(len(payload))
    for y in range(height):
        for x in range(width):
            morton = ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) |
                      ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3))
            src = (((y >> 3) * (width >> 3) + (x >> 3)) << 6) + morton
            si = src * 4
            di = ((height - 1 - y) * width + x) * 4
            a, b, g, r = payload[si:si + 4]
            output[di:di + 4] = bytes((r, g, b, a))
    return bytes(output)


def png_chunk(label, data):
    return (struct.pack('>I', len(data)) + label + data +
            struct.pack('>I', zlib.crc32(label + data) & 0xffffffff))


def encode_rgba_png(rgba, width, height):
    if len(rgba) != width * height * 4:
        raise ValueError('invalid RGBA raster')
    scanlines = b''.join(b'\0' + rgba[y * width * 4:(y + 1) * width * 4]
                         for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' +
            png_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) +
            png_chunk(b'IDAT', zlib.compress(scanlines, level=9)) +
            png_chunk(b'IEND', b''))


def quantize_a1rgb555(rgba):
    if len(rgba) % 4:
        raise ValueError('invalid RGBA input')
    result = bytearray(len(rgba) // 2)
    for index in range(0, len(rgba), 4):
        r, g, b, a = rgba[index:index + 4]
        value = ((0x8000 if a >= 128 else 0) | (b >> 3) << 10 |
                 (g >> 3) << 5 | (r >> 3))
        struct.pack_into('<H', result, index // 2, value)
    return bytes(result)


def recover(archive, output):
    archive, output = Path(archive), Path(output)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('private source archive missing or symlink')
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError('private output must be absent in an existing directory')
    textures = []
    decoded = []
    distribution = Counter()
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        names = [i.filename for i in members]
        if len(names) != len(set(names)):
            raise ValueError('ambiguous source ZIP duplicate paths')
        for info in members:
            name = info.filename
            if (not name or name.startswith('/') or '\\' in name or
                    any(x in ('', '.', '..') for x in name.rstrip('/').split('/')) or
                    stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError('unsafe source ZIP path')
        for base in EXPECTED:
            entry = f'decoded_c5/gui/{base}.c5'
            if entry not in names or not 0 < source.getinfo(entry).file_size <= MAX_C5:
                raise ValueError('missing or oversized source GUI C5: ' + base)
            c5 = source.read(entry)
            rows, start = descriptors(c5)
            for row in rows:
                path = f'{base}/t{row["index"]:02d}_{row["name"]}'
                row['source'] = entry
                row['original_c5_sha256'] = sha256(c5)
                row['output_base'] = path if row['rgba8_decoder_supported'] else None
                key = f'{row["bits_per_pixel"]}-bit token {row["token"]}'
                distribution[key] += 1
                textures.append(row)
                if row['rgba8_decoder_supported']:
                    position = start + row['gpu_offset']
                    gpu = c5[position:position + row['gpu_bytes']]
                    rgba = decode_morton_abgr8(gpu, row['width'], row['height'])
                    png = encode_rgba_png(rgba, row['width'], row['height'])
                    native = quantize_a1rgb555(rgba)
                    row['original_rgba_sha256'] = sha256(rgba)
                    row['png_sha256'] = sha256(png)
                    row['ds_a1rgb555_sha256'] = sha256(native)
                    decoded.append((path, png, native))
    if len(textures) != 132 or len(decoded) != 35:
        raise ValueError('C351 original 16-resource source texture roster changed')
    report = {
        'schema': 'c351-original-gui-texture-atlas-decode-v1',
        'original_source_archive_sha256': sha256(archive.read_bytes()),
        'original_c5_resources': len(EXPECTED),
        'total_original_texture_descriptors': len(textures),
        'confirmed_abgr8_rgba_atlases_decoded': len(decoded),
        'other_format_descriptors_preserved_undecoded': len(textures) - len(decoded),
        'source_format_counts': dict(sorted(distribution.items())),
        'texture_entries': textures,
        'source_decoded_rgba8_texture_atlases': True,
        'native_atlas_A1RGB555_conversion': True,
        'complete_original_gui_format_coverage': False,
        'original_gui_screen_layout_complete': False,
        'original_3ds_visual_parity_verified': False,
        'original_game_release_ready': False,
    }
    with tempfile.TemporaryDirectory(prefix='.c351-', dir=output.parent) as d:
        root = Path(d)
        for path, png, native in decoded:
            dest = root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.with_suffix('.png').write_bytes(png)
            dest.with_suffix('.rgb555').write_bytes(native)
            if sha256(dest.with_suffix('.png').read_bytes()) != sha256(png):
                raise ValueError('private PNG failed writeback verification')
        (root / 'C351_PRIVATE_TEXTURE_ATLASES.json').write_text(json.dumps(report, indent=2) + '\n')
        os.rename(root, output)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = recover(a.archive, a.output)
    print(json.dumps({k:r[k] for k in ('original_c5_resources',
      'total_original_texture_descriptors', 'confirmed_abgr8_rgba_atlases_decoded',
      'other_format_descriptors_preserved_undecoded', 'source_format_counts')}, indent=2))
    print('C351: Atlas images only, NOT full original two-screen art.')
