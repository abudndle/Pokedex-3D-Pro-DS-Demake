#!/usr/bin/env python3
"""C350: recover exact original 3DS GUI GPU payload byte ranges privately.

C5 header byte count 0x04 is metadata size after the 0x78 header; 0x08
is trailing GPU resource size. This validates source boundaries, verifies
original nested C5 metadata, and deduplicates language-identical byte blobs.
Outputs are raw 3DS GPU bytes, NOT decoded 2D UI or DS-compatible screens.
NEVER commit extracted files to a public repository or public CI artifacts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
import zipfile

HEADER_SIZE = 0x78
ROOT_MAGIC = b'\xc5\x78\x00\x01'
NESTED_MAGIC = b'\xc5\x78\x00\x02'
MAX_CONTAINER = 12 * 1024 * 1024
EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def split_gpu_container(data):
    """Prove C5 metadata and trailing GPU segment are disjoint/in-bounds."""
    if not HEADER_SIZE + 256 <= len(data) <= MAX_CONTAINER or data[:4] != ROOT_MAGIC:
        raise ValueError('invalid original GUI C5 header or byte count')
    metadata_size, gpu_size = struct.unpack_from('<II', data, 4)
    boundary = HEADER_SIZE + metadata_size
    if (metadata_size < HEADER_SIZE or not 256 <= gpu_size <= MAX_CONTAINER or
            gpu_size % 256 or boundary + gpu_size != len(data)):
        raise ValueError('inconsistent GUI C5 metadata/GPU boundary')
    # Metadata includes a C5 v2 resource directory described by C347. It must
    # never overlap the trailing GPU payload or point beyond the end of source.
    inner_offset = struct.unpack_from('<I', data, 0x68)[0]
    if not HEADER_SIZE <= inner_offset <= boundary - 8:
        raise ValueError('nested GUI C5 offset outside metadata region')
    if data[inner_offset:inner_offset + 4] != NESTED_MAGIC:
        raise ValueError('nested GUI C5 header magic mismatch')
    inner_length = struct.unpack_from('<I', data, inner_offset + 4)[0]
    if inner_length < HEADER_SIZE or inner_offset + inner_length > boundary:
        raise ValueError('nested C5 metadata overlaps GPU payload')
    return boundary, data[boundary:]


def recover(archive, output):
    """Write de-duplicated original GPU byte regions atomically to PRIVATE output."""
    archive, output = Path(archive), Path(output)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('source archive missing or symlink')
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError('private output directory must not exist; parent must exist')
    sources, blobs, rows = {}, {}, []
    with zipfile.ZipFile(archive) as source:
        info = source.infolist()
        names = [m.filename for m in info]
        if len(names) != len(set(names)):
            raise ValueError('duplicate CCI source archive path')
        for member in info:
            path = member.filename
            if (not path or path.startswith('/') or '\\' in path or
                    any(part in ('', '.', '..') for part in path.rstrip('/').split('/')) or
                    stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError('unsafe CCI source archive path')
        for key in EXPECTED:
            member = f'decoded_c5/gui/{key}.c5'
            if member not in names:
                raise ValueError('missing original GUI C5 source: ' + key)
            size = source.getinfo(member).file_size
            if not 0 < size <= MAX_CONTAINER:
                raise ValueError('original GUI source exceeds size limit')
            raw = source.read(member)
            if len(raw) != size:
                raise ValueError('truncated original GUI C5 source')
            offset, gpu = split_gpu_container(raw)
            sha = digest(gpu)
            if sha in blobs and blobs[sha] != gpu:
                raise ValueError('SHA collision with distinct original GPU payload')
            blobs[sha] = gpu
            sources[key] = sha
            rows.append({'source': member, 'original_sha256': digest(raw),
                         'gpu_start': offset, 'gpu_bytes': len(gpu),
                         'gpu_sha256': sha, 'private_blob': f'gpu/{sha}.bin'})
    for page in range(1, 7):
        a, b = sources[f'en/gui{page:02d}'], sources[f'jp/gui{page:02d}']
        if a != b:
            raise ValueError(f'English/Japanese page {page} GPU source mismatch')
    # This source-observed six-pair crosscheck is intentionally not a claim that
    # other language-specific textures (e.g. title) must also be identical.
    report = {
        'schema': 'c350-original-gui-gpu-source-payloads-v1',
        'source_archive_sha256': digest(archive.read_bytes()),
        'source_gui_c5_files': len(rows),
        'unique_original_gpu_blobs': len(blobs),
        'original_gpu_total_bytes': sum(r['gpu_bytes'] for r in rows),
        'unique_original_gpu_bytes': sum(map(len, blobs.values())),
        'en_jp_numbered_gui_gpu_pairs_identical': 6,
        'entries': rows,
        'original_GPU_bytes_recovered': True,
        'original_texture_pixel_formats_decoded': False,
        'original_texture_atlas_regions_mapped': False,
        'ds_ui_screen_bitmaps_ready': False,
        'original_game_release_ready': False,
    }
    with tempfile.TemporaryDirectory(prefix='.c350-', dir=output.parent) as temp:
        stage = Path(temp)
        (stage / 'gpu').mkdir()
        for sha, blob in sorted(blobs.items()):
            dest = stage / 'gpu' / f'{sha}.bin'
            dest.write_bytes(blob)
            if digest(dest.read_bytes()) != sha:
                raise ValueError('private GPU payload failed writeback verification')
        (stage / 'C350_PRIVATE_GPU_SOURCES.json').write_text(
            json.dumps(report, indent=2) + '\n')
        os.rename(stage, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    a = parser.parse_args()
    r = recover(a.archive, a.output)
    print(json.dumps({k:r[k] for k in (
        'source_gui_c5_files', 'unique_original_gpu_blobs',
        'original_gpu_total_bytes', 'unique_original_gpu_bytes',
        'en_jp_numbered_gui_gpu_pairs_identical')}, indent=2))
    print('NOTE: original GPU bytes, NOT DS-renderable original GUI bitmaps')


if __name__ == '__main__':
    main()
