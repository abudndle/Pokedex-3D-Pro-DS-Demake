#!/usr/bin/env python3
"""C357: preserve source-authentic GUI C5 v2 3x4 object-transform records.

The nested C5 v2 section offsets at +0x38/+0x3c delimit 56-byte
records. Each record holds 12 little-endian IEEE-754 float32 coefficients
and 2 opaque 32-bit words. These are original SCENE transforms, NOT
measured DS screen coordinates, texture UV rectangles or HOME hitboxes.

Original-derived reports must stay in a PRIVATE repository. Public tests
use only synthetic C5 resources generated in memory.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
import zipfile

ORIGINAL_MAGIC = b'\xc5\x78\x00\x01'
SCENE_MAGIC = b'\xc5\x78\x00\x02'
OUTER_HEADER = 0x78
INNER_HEADER = 0x78
MATRIX_RECORD_BYTES = 56
MAX_C5 = 12 * 1024 * 1024
EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))
EXPECTED_COUNTS = {
    'gui_title': 16,
    'gui_common': 5,
    'en/gui_title': 11,
    'jp/gui_title': 10,
    **{f'{lang}/gui{i:02d}': 3 for lang in ('en', 'jp') for i in range(1, 7)},
}


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def decode_source_transforms(data):
    """Decode source-observed scene transforms with exact original byte offsets."""
    if (not OUTER_HEADER + INNER_HEADER <= len(data) <= MAX_C5 or
            data[:4] != ORIGINAL_MAGIC):
        raise ValueError('original C5 header/length mismatch')
    meta_bytes, gpu_bytes = struct.unpack_from('<II', data, 4)
    gpu_start = OUTER_HEADER + meta_bytes
    if not meta_bytes or not gpu_bytes or gpu_start + gpu_bytes != len(data):
        raise ValueError('original C5 metadata/GPU extents inconsistent')
    inner_offset = struct.unpack_from('<I', data, 0x68)[0]
    if not OUTER_HEADER <= inner_offset <= gpu_start - INNER_HEADER:
        raise ValueError('nested scene header outside C5 metadata')
    if data[inner_offset:inner_offset+4] != SCENE_MAGIC:
        raise ValueError('nested scene C5 v2 magic mismatch')
    inner_bytes = struct.unpack_from('<I', data, inner_offset + 4)[0]
    if inner_bytes < INNER_HEADER or inner_offset + inner_bytes > gpu_start:
        raise ValueError('nested scene C5 v2 extents outside metadata')
    transforms_start, transforms_end = struct.unpack_from('<II', data, inner_offset + 0x38)
    if (not INNER_HEADER <= transforms_start < transforms_end <= inner_bytes or
            (transforms_end - transforms_start) % MATRIX_RECORD_BYTES):
        raise ValueError('invalid 56-byte original GUI scene transform section')
    num = (transforms_end - transforms_start) // MATRIX_RECORD_BYTES
    if not 1 <= num <= 64:
        raise ValueError('unsupported source GUI node count')
    chunk = data[inner_offset + transforms_start:inner_offset + transforms_end]
    nodes = []
    for i in range(num):
        pos = inner_offset + transforms_start + i*MATRIX_RECORD_BYTES
        vals = struct.unpack_from('<12f', data, pos)
        if any(not math.isfinite(v) or abs(v) > 16384 for v in vals):
            raise ValueError('nonfinite/out-of-bounds source transform coefficient')
        opaque = struct.unpack_from('<2I', data, pos + 48)
        record = data[pos:pos+MATRIX_RECORD_BYTES]
        nodes.append({
            'index': i, 'original_c5_byte_offset': pos,
            'nested_c5_relative_byte_offset': transforms_start + i*MATRIX_RECORD_BYTES,
            'original_transform_record_sha256': sha(record),
            'matrix_3x4_row_major': [list(vals[j:j+4]) for j in (0, 4, 8)],
            'source_translation_xyz': [vals[3], vals[7], vals[11]],
            'matrix_float32_word_bits': [f'{word:08x}' for word in struct.unpack_from('<12I', data, pos)],
            'opaque_original_metadata_words': [f'{word:08x}' for word in opaque],
            'original_scene_position_proven': True,
            'original_screen_pixel_position_proven': False,
            'original_touch_rectangle_proven': False,
        })
    return {
        'original_c5_sha256': sha(data),
        'nested_scene_header_offset': inner_offset,
        'nested_scene_header_bytes': inner_bytes,
        'transform_section_relative_begin': transforms_start,
        'transform_section_relative_end': transforms_end,
        'transform_section_sha256': sha(chunk),
        'source_transform_records': num,
        'transforms': nodes,
    }


def recover(archive):
    archive = Path(archive)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('private source CCI archive unavailable or symlink')
    result = {}
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError('ambiguous duplicate CCI source ZIP paths')
        for item in infos:
            p = item.filename
            if (not p or p.startswith('/') or '\\' in p or
                any(x in ('', '.', '..') for x in p.rstrip('/').split('/')) or
                stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError('unsafe private source ZIP path')
        for key in EXPECTED:
            name = f'decoded_c5/gui/{key}.c5'
            if name not in names or not OUTER_HEADER + INNER_HEADER <= z.getinfo(name).file_size <= MAX_C5:
                raise ValueError('missing or oversized original GUI C5: '+key)
            raw = z.read(name)
            row = decode_source_transforms(raw)
            if row['source_transform_records'] != EXPECTED_COUNTS[key]:
                raise ValueError('source GUI scene roster has changed: '+key)
            result[key] = row
    for i in range(1, 7):
        a, b = result[f'en/gui{i:02d}'], result[f'jp/gui{i:02d}']
        if a['transform_section_sha256'] != b['transform_section_sha256']:
            raise ValueError(f'original English/Japanese GUI page {i} transforms differ')
    total = sum(x['source_transform_records'] for x in result.values())
    if len(result) != 16 or total != 78:
        raise ValueError('original source scene count does not match observed roster')
    return {
        'schema': 'c357-private-original-gui-scene-transforms-v1',
        'source_archive_sha256': sha(archive.read_bytes()),
        'original_c5_resources': len(result),
        'source_observed_transform_records': total,
        'source_title_scene_transforms': sum(result[x]['source_transform_records'] for x in
                                             ('gui_title', 'en/gui_title', 'jp/gui_title')),
        'matching_japanese_english_gui_page_sections': 6,
        'source_scene_transform_positions_extracted': True,
        'source_scene_to_screen_projection_decoded': False,
        'original_title_screen_composition_verified': False,
        'original_home_touch_geometry_verified': False,
        'original_release_framebuffers_reconstructed': False,
        'unrecovered_release_files_remaining': 16,
        'release_ready': False,
        'source_original_c5_transforms': result,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.report.is_symlink() or a.report.exists() or not a.report.parent.is_dir():
        raise SystemExit('Refusing overwrite or missing private output parent')
    result = recover(a.archive)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: result[k] for k in (
        'original_c5_resources', 'source_observed_transform_records',
        'source_title_scene_transforms', 'matching_japanese_english_gui_page_sections',
        'source_scene_to_screen_projection_decoded', 'release_ready')}, indent=2))


if __name__ == '__main__':
    main()
