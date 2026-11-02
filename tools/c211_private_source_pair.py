#!/usr/bin/env python3
"""Fail-closed private C5/OBJ/P3VX/P3IX source-to-native geometry pair gate.

The P3IX must reproduce an independently verified original primitive manifest;
the P3VX must reproduce uniquely matched C5 XYZ. This is NOT proof of complete
models, materials, animation or real emulator rendering. Never publish inputs.
"""
import argparse
import json
from pathlib import Path
import struct
import zlib

MAX_MESHES = 64
MAX_VERTICES = 8192
MAX_TRIANGLES = 1800
MAX_VX_BYTES = 16 + MAX_MESHES * 8 + MAX_VERTICES * 6
MAX_IX_BYTES = 10 + MAX_MESHES * 6 + MAX_TRIANGLES * 6


def validate_native_pair(vx, ix, model):
    """Verify native pair identity, CRC, mesh ownership, and DS geometry budget."""
    if type(model) is not int or not 0 <= model <= 733 or 721 <= model <= 724:
        raise ValueError('invalid model identity')
    if not 16 <= len(vx) <= MAX_VX_BYTES or vx[:4] != b'P3VX':
        raise ValueError('invalid P3VX size or magic')
    version, owner, mesh_count, reserved, crc = struct.unpack_from('<HHHHI', vx, 4)
    if version != 1 or owner != model or reserved or not 1 <= mesh_count <= MAX_MESHES:
        raise ValueError('invalid P3VX identity or mesh count')
    if zlib.crc32(vx[16:]) & 0xffffffff != crc:
        raise ValueError('P3VX CRC mismatch')
    table_end = 16 + 8 * mesh_count
    if len(vx) < table_end:
        raise ValueError('truncated P3VX table')
    counts = {}
    first = 0
    previous = -1
    for offset in range(16, table_end, 8):
        mesh, count, start = struct.unpack_from('<HHI', vx, offset)
        if mesh <= previous or mesh >= MAX_MESHES or count < 3 or start != first:
            raise ValueError('invalid P3VX mesh descriptor')
        previous = mesh
        counts[mesh] = count
        first += count
        if first > MAX_VERTICES:
            raise ValueError('P3VX vertex budget exceeded')
    if len(vx) != table_end + first * 6:
        raise ValueError('P3VX vertex payload mismatch')
    if not 16 <= len(ix) <= MAX_IX_BYTES or ix[:4] != b'P3IX':
        raise ValueError('invalid P3IX size or magic')
    version, owner, meshes = struct.unpack_from('<HHH', ix, 4)
    if version != 1 or owner != model or not 1 <= meshes <= MAX_MESHES:
        raise ValueError('invalid P3IX identity or mesh count')
    position = 10
    triangles = 0
    previous = -1
    for _ in range(meshes):
        if len(ix) - position < 6:
            raise ValueError('truncated P3IX descriptor')
        mesh, count = struct.unpack_from('<HI', ix, position)
        position += 6
        if mesh <= previous or mesh not in counts or not 1 <= count <= MAX_TRIANGLES - triangles:
            raise ValueError('P3IX mesh mismatch or DS triangle budget exceeded')
        previous = mesh
        if count * 6 > len(ix) - position:
            raise ValueError('truncated P3IX triangles')
        for offset in range(position, position + count * 6, 6):
            a, b, c = struct.unpack_from('<HHH', ix, offset)
            if a == b or b == c or a == c or max(a, b, c) >= counts[mesh]:
                raise ValueError('invalid source triangle vertex ownership')
        position += count * 6
        triangles += count
    if position != len(ix):
        raise ValueError('trailing P3IX bytes')
    return {'model': model, 'vertex_meshes': len(counts),
            'verified_index_meshes': meshes, 'vertices': first,
            'triangles': triangles, 'complete_original_model_verified': False,
            'private_asset_emulator_verified': False}


def validate_source_pair(c5, obj, manifest, vx, ix, model):
    """Require both independent source-evidence exporters to reproduce the pair."""
    from c207_private_c5_xyz import convert
    from c173_verified_primitive_export import export
    descriptors, expected_vx = convert(c5, obj, model)
    if vx != expected_vx:
        raise ValueError('P3VX differs from independently matched C5 XYZ')
    if ix != export(manifest, c5):
        raise ValueError('P3IX differs from verified original primitive map')
    result = validate_native_pair(vx, ix, model)
    result['source_xyz_descriptors'] = len(descriptors)
    result['source_triangle_manifest_verified'] = True
    return result


def main():
    from c207_private_c5_xyz import private_path, read_bounded
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('c5', 'obj', 'manifest', 'p3vx', 'p3ix'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    paths = {name: private_path(getattr(args, name)) for name in
             ('c5', 'obj', 'manifest', 'p3vx', 'p3ix')}
    stem = paths['c5'].stem
    if len(stem) != 4 or stem[0] != 'p' or not stem[1:].isdigit():
        parser.error('expected pNNN private model filenames')
    if any(paths[name].name != stem + '.' + name for name in ('c5', 'obj', 'p3vx', 'p3ix')):
        parser.error('private source and geometry filenames must match')
    if paths['manifest'].name != stem + '.json':
        parser.error('private verified primitive manifest must match model')
    model = int(stem[1:])
    c5, obj = read_bounded(paths['c5']), read_bounded(paths['obj'])
    if paths['manifest'].stat().st_size > 2 * 1024 * 1024:
        raise ValueError('oversized private manifest')
    manifest = json.loads(read_bounded(paths['manifest']))
    vx, ix = read_bounded(paths['p3vx']), read_bounded(paths['p3ix'])
    result = validate_source_pair(c5, obj, manifest, vx, ix, model)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
