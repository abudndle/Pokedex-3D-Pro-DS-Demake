#!/usr/bin/env python3
"""C352: decode source-authentic 3DS C5 GUI PICA texture formats privately.

Formats: RGBA8, RGB8, L8, LA8, RGBA4. Yields source-provenanced PNG
atlases and DS A1RGB555 atlas candidates; original dual-screen layout,
composition and ROM art integration remain unverified. Keep results private.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import zipfile

from c351_gui_texture_atlases import (EXPECTED, MAX_C5, descriptors,
    decode_morton_abgr8, encode_rgba_png, quantize_a1rgb555)

FORMAT_NAMES = {
    0x14016752: 'RGBA8',
    0x14016754: 'RGB8',
    0x14016757: 'L8',
    0x14016758: 'LA8',
    0x80336752: 'RGBA4',
}
BPP = {'RGBA8': 4, 'RGB8': 3, 'L8': 1, 'LA8': 2, 'RGBA4': 2}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def morton_index(x, y, width):
    within = ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) |
              ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3))
    return (((y >> 3) * (width >> 3) + (x >> 3)) << 6) + within


def texel_color(data, pos, kind):
    if kind == 'RGBA8':
        a, b, g, r = data[pos:pos + 4]
        return r, g, b, a
    if kind == 'RGB8':
        b, g, r = data[pos:pos + 3]
        return r, g, b, 255
    if kind == 'LA8':
        a, l = data[pos:pos + 2]
        return l, l, l, a
    if kind == 'L8':
        l = data[pos]
        return l, l, l, 255
    if kind == 'RGBA4':
        word = int.from_bytes(data[pos:pos + 2], 'little')
        return ((word >> 12 & 15) * 17, (word >> 8 & 15) * 17,
                (word >> 4 & 15) * 17, (word & 15) * 17)
    raise ValueError('unsupported PICA texture format')


def decode_pica_gui(data, width, height, token):
    kind = FORMAT_NAMES.get(token)
    if kind is None:
        raise ValueError('unknown PICA texture token')
    if (type(width) is not int or type(height) is not int or
            width < 8 or height < 8 or width > 1024 or height > 1024 or
            width & (width - 1) or height & (height - 1) or
            len(data) != width * height * BPP[kind]):
        raise ValueError('invalid PICA GUI image dimensions/byte count')
    if kind == 'RGBA8':
        return decode_morton_abgr8(data, width, height)
    out = bytearray(width * height * 4)
    step = BPP[kind]
    for y in range(height):
        dst_y = height - 1 - y
        for x in range(width):
            src = morton_index(x, y, width) * step
            dst = (dst_y * width + x) * 4
            out[dst:dst + 4] = bytes(texel_color(data, src, kind))
    return bytes(out)


def recover(archive, output):
    archive, output = Path(archive), Path(output)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('private original archive missing or symlink')
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError('private output already exists or parent missing')
    rows = []
    rendered = []
    counts = collections.Counter()
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [x.filename for x in infos]
        if len(names) != len(set(names)):
            raise ValueError('duplicate original C5 source archive paths')
        for info in infos:
            n = info.filename
            if (not n or n.startswith('/') or '\\' in n or
                    any(part in ('', '.', '..') for part in n.rstrip('/').split('/')) or
                    stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError('unsafe private C5 archive path')
        for base in EXPECTED:
            name = f'decoded_c5/gui/{base}.c5'
            if name not in names or not 0 < z.getinfo(name).file_size <= MAX_C5:
                raise ValueError('missing or oversized C5 GUI source: ' + base)
            raw = z.read(name)
            descriptors_rows, start = descriptors(raw)
            for item in descriptors_rows:
                token = int(item['token'], 16)
                if token not in FORMAT_NAMES:
                    raise ValueError('C352 unknown texture descriptor token')
                kind = FORMAT_NAMES[token]
                off = start + item['gpu_offset']
                blob = raw[off:off + item['gpu_bytes']]
                pixels = decode_pica_gui(blob, item['width'], item['height'], token)
                png = encode_rgba_png(pixels, item['width'], item['height'])
                native = quantize_a1rgb555(pixels)
                stem = f'{base}/t{item["index"]:02d}_{item["name"]}'
                row = {**item, 'format_name': kind, 'original_source': name,
                       'original_c5_sha256': sha(raw), 'png_path': stem + '.png',
                       'png_sha256': sha(png), 'rgba_raster_sha256': sha(pixels),
                       'ds_atlas_path': stem + '.rgb555',
                       'ds_atlas_sha256': sha(native), 'ds_atlas_bytes': len(native),
                       'full_original_ui_layout_verified': False}
                rows.append(row)
                counts[kind] += 1
                rendered.append((stem, png, native))
    if len(rows) != 132 or counts != {
        'RGBA8': 35, 'LA8': 72, 'L8': 14, 'RGB8': 6, 'RGBA4': 5,
    }:
        raise ValueError('C352 source roster/format counts unexpected')
    report = {
        'schema': 'c352-original-gui-all-observed-pica-uncompressed-formats-v1',
        'private_source_archive_sha256': sha(archive.read_bytes()),
        'source_c5_count': len(EXPECTED),
        'source_texture_entries': len(rows),
        'decoded_textures': len(rendered),
        'decoded_by_format': dict(sorted(counts.items())),
        'lossless_png_atlases': len(rendered),
        'ds_a1rgb555_atlas_candidates': len(rendered),
        'all_original_GUI_texture_entry_formats_decoded': True,
        'source_exact_3ds_screen_compositing_verified': False,
        'original_dual_screen_ui_pages_ready': False,
        'DS_NitroFS_uses_new_atlases': False,
        'asset_integrated_ROM_with_original_GUI_verified': False,
        'original_game_release_ready': False,
        'entries': rows,
    }
    with tempfile.TemporaryDirectory(prefix='.c352-', dir=output.parent) as tmp:
        stage = Path(tmp)
        for stem, png, native in rendered:
            path = stage / stem
            path.parent.mkdir(parents=True, exist_ok=True)
            path.with_suffix('.png').write_bytes(png)
            path.with_suffix('.rgb555').write_bytes(native)
            if sha(path.with_suffix('.png').read_bytes()) != sha(png):
                raise ValueError('PNG private writeback hash mismatch')
            if sha(path.with_suffix('.rgb555').read_bytes()) != sha(native):
                raise ValueError('DS atlas private writeback hash mismatch')
        (stage / 'C352_PRIVATE_TEXTURE_FORMATS.json').write_text(
            json.dumps(report, indent=2) + '\n')
        os.rename(stage, output)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    result = recover(a.archive, a.output)
    print(json.dumps({k: result[k] for k in (
        'source_texture_entries', 'decoded_textures', 'decoded_by_format',
        'original_game_release_ready')}, indent=2))
