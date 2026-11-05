#!/usr/bin/env python3
"""C357: recover source-authentic C5 GUI node 3x4 transform matrices.

The original 3DS C5 v2 embedded metadata contains an offset-bounded block
of 56-byte node records (48 bytes row-major float32 + 8 opaque bytes).
These are source scene-space transforms, NOT calibrated DS pixel locations,
rendering order, seven-icon HOME touch boxes, or final screen compositions.
Generate reports with original game numeric values only in PRIVATE storage.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
import zipfile

EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))
MAX_C5 = 12 * 1024 * 1024
RECORD_SIZE = 56
ROOT = b'\xc5\x78\x00\x01'
EMBEDDED = b'\xc5\x78\x00\x02'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_scene_transforms(data):
    """Decode only proven 3x4 matrices and preserve unknown metadata verbatim."""
    if not 0x78 + 0x78 + 256 <= len(data) <= MAX_C5 or data[:4] != ROOT:
        raise ValueError('invalid C5 root magic or container length')
    metadata, gpu = struct.unpack_from('<II', data, 4)
    end = 0x78 + metadata
    if metadata < 0x78 or gpu < 256 or end + gpu != len(data):
        raise ValueError('invalid C5 metadata and GPU container boundaries')
    pos = struct.unpack_from('<I', data, 0x68)[0]
    if pos < 0x78 or pos + 0x78 > end or data[pos:pos+4] != EMBEDDED:
        raise ValueError('invalid embedded C5 v2 source location or magic')
    inner_length = struct.unpack_from('<I', data, pos + 4)[0]
    if not 0x78 <= inner_length <= end - pos:
        raise ValueError('invalid embedded C5 declared size')
    section_start, section_end = struct.unpack_from('<II', data, pos+0x38)
    if not 0x78 <= section_start < section_end <= inner_length:
        raise ValueError('invalid C5 node transform section bounds')
    section_size = section_end - section_start
    if section_size % RECORD_SIZE or not 1 <= section_size // RECORD_SIZE <= 32:
        raise ValueError('C5 node transform section does not contain complete 56-byte records')
    absolute = pos+section_start
    section = data[absolute:pos+section_end]
    entries = []
    for i in range(section_size // RECORD_SIZE):
        start = i*RECORD_SIZE
        floats = struct.unpack_from('<12f', section, start)
        if any(not math.isfinite(value) or abs(value) > 1_000_000 for value in floats):
            raise ValueError('nonfinite or out-of-range original C5 node transform')
        raw = section[start:start+RECORD_SIZE]
        words = struct.unpack_from('<12I', raw)
        entries.append({
            'index':i,
            'source_matrix_offset':absolute+start,
            'source_record_sha256':sha(raw),
            'original_float_words_hex':[f'{word:08x}' for word in words],
            'matrix_rows':[list(floats[j:j+4]) for j in (0,4,8)],
            'translation':[floats[j] for j in (3,7,11)],
            'tail_hex':[raw[48:52].hex(),raw[52:56].hex()],
            'native_3ds_scene_coordinates_only':True,
            'authentic_screen_pixel_coordinates_verified':False,
        })
    return {
        'source_c5_sha256':sha(data),
        'embedded_c5_offset':pos,
        'embedded_declared_bytes':inner_length,
        'source_section_start':absolute,
        'source_section_end':pos+section_end,
        'source_transform_section_sha256':sha(section),
        'count':len(entries),
        'transform_tail_semantics_decoded':False,
        'transforms':entries,
    }


def recover(archive):
    archive = Path(archive)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('missing or symlinked original private CCI archive')
    resources = {}
    raw_sections = {}
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        names = [m.filename for m in members]
        if len(names) != len(set(names)):
            raise ValueError('duplicate original CCI source ZIP paths')
        for member in members:
            p = member.filename
            if (not p or p.startswith('/') or '\\' in p or
                any(part in ('', '.', '..') for part in p.rstrip('/').split('/')) or
                stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('unsafe original source archive path')
        for key in EXPECTED:
            path = f'decoded_c5/gui/{key}.c5'
            if path not in names or not 0 < z.getinfo(path).file_size <= MAX_C5:
                raise ValueError('missing or oversized original C5 GUI source: '+key)
            data = z.read(path)
            if len(data) != z.getinfo(path).file_size:
                raise ValueError('truncated original C5 input')
            entry = parse_scene_transforms(data)
            resources[key] = entry
            raw_sections[key] = data[entry['source_section_start']:entry['source_section_end']]
    for i in range(1, 7):
        en, jp = f'en/gui{i:02d}', f'jp/gui{i:02d}'
        if raw_sections[en] != raw_sections[jp]:
            raise ValueError(f'different original EN/JP numbered GUI node transforms: {i}')
    counts = {key:resources[key]['count'] for key in EXPECTED}
    expected = {'gui_title':16, 'gui_common':5, 'en/gui_title':11, 'jp/gui_title':10,
                **{f'{lang}/gui{i:02d}':3 for lang in ('en','jp') for i in range(1,7)}}
    if counts != expected:
        raise ValueError('original C5 GUI transform roster changed')
    return {
        'schema':'c357-original-gui-c5-embedded-scene-node-transforms-v1',
        'source_archive_sha256':sha(archive.read_bytes()),
        'original_c5_resources':len(resources),
        'original_transform_records':sum(counts.values()),
        'identical_en_jp_numbered_gui_transform_pairs':6,
        'per_resource_transform_counts':counts,
        'original_scene_node_transform_format':'12 little-endian IEEE754 float32, 3x4 row-major + 8 opaque bytes',
        'original_native_scene_transform_bytes_recovered':True,
        'transform_tail_meanings_verified':False,
        'native_3ds_coordinates_calibrated_to_DS_pixels':False,
        'original_texture_atlas_to_mesh_mapping_verified':False,
        'source_authentic_title_256x192_frame_composed':False,
        'source_authentic_home_touch_geometry_measured':False,
        'original_missing_release_targets_remaining':16,
        'release_ready':False,
        'resources':resources,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    args=p.parse_args()
    if args.report.is_symlink() or args.report.exists() or not args.report.parent.is_dir():
        raise SystemExit('output requires an absent path inside an existing PRIVATE directory')
    result=recover(args.archive)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:result[k] for k in (
        'original_c5_resources','original_transform_records',
        'identical_en_jp_numbered_gui_transform_pairs',
        'native_3ds_coordinates_calibrated_to_DS_pixels',
        'original_missing_release_targets_remaining','release_ready')},indent=2))


if __name__ == '__main__':
    main()
