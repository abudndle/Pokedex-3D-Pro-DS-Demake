#!/usr/bin/env python3
"""C245: fail-closed private C5 ordered XYZ + exact face bytes -> native pair.

The C62 OBJ is source-derived, NOT an independent renderer capture. This
verifies only untextured position/index transport. It does not certify original
material, UV seam identity, skinning, animations, or asset-integrated gameplay.
No original input, converted model, report, or SHA belongs in public GitHub.
"""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import shutil
import struct
import tempfile

MAX_MESHES = 64
MAX_VERTICES = 8192
MAX_TRIANGLES = 1800
MAX_ERROR = 1.0 / 8192.0 + 1e-12


def pack_index_stream(vertex_counts, index_counts, faces, model):
    """Build native P3IX only for ordered descriptor-local triangle faces."""
    if type(model) is not int or not 0 <= model <= 733 or 721 <= model <= 724:
        raise ValueError('invalid model identity')
    if not 1 <= len(vertex_counts) == len(index_counts) <= MAX_MESHES:
        raise ValueError('invalid mesh count')
    if sum(vertex_counts) > MAX_VERTICES or sum(index_counts) // 3 > MAX_TRIANGLES:
        raise ValueError('native DS geometry budget exceeded')
    if any(type(n) is not int or n < 3 or n > 65535 for n in vertex_counts):
        raise ValueError('invalid source vertex counts')
    if any(type(n) is not int or n < 3 or n % 3 for n in index_counts):
        raise ValueError('invalid source index counts')
    if len(faces) != sum(index_counts) // 3:
        raise ValueError('incomplete source face coverage')
    result = bytearray(struct.pack('<4sHHH', b'P3IX', 1, model, len(vertex_counts)))
    base = face_pos = 0
    for mesh, (vertices, indices) in enumerate(zip(vertex_counts, index_counts)):
        result += struct.pack('<HI', mesh, indices // 3)
        for face in faces[face_pos:face_pos + indices // 3]:
            if (len(face) != 3 or any(type(v) is not int or not base <= v < base + vertices for v in face)):
                raise ValueError('source face crosses descriptor mesh partition')
            local = tuple(v - base for v in face)
            if len(set(local)) != 3:
                raise ValueError('degenerate source face')
            result += struct.pack('<3H', *local)
        base += vertices
        face_pos += indices // 3
    return bytes(result)


def verify_ordered_xyz(c5, meta, obj_xyz, descriptor_shifts):
    """Require each original 28-byte record to match its exact OBJ vertex slot.

    A multiset-only match is insufficient: face indices refer to vertex slots,
    and swapping two distinct slots can silently corrupt original topology.
    """
    first = meta['first_table']
    if [mesh for mesh, _ in descriptor_shifts] != list(range(len(first))):
        raise ValueError('partial or nonsequential original XYZ descriptors')
    if len(obj_xyz) != sum(row['record_count'] for row in first):
        raise ValueError('OBJ vertex count differs from original C5 descriptors')
    pos = 0
    max_error = 0.0
    seam_duplicates = 0
    for mesh, ((idx, shift), row) in enumerate(zip(descriptor_shifts, first)):
        count = row['record_count']
        start = int(row['data_offset'], 16)
        if idx != mesh or row['low_byte_of_upper16'] != 28 or shift not in (0, 4, 8, 12, 16):
            raise ValueError('unsupported source XYZ record layout')
        if start < 0 or start + count * 28 > len(c5):
            raise ValueError('original XYZ record exceeds source bounds')
        mesh_positions = []
        for slot in range(count):
            original = struct.unpack_from('<3f', c5, start + slot * 28 + shift)
            reference = obj_xyz[pos + slot]
            if not all(math.isfinite(value) for value in original):
                raise ValueError('nonfinite original XYZ')
            if struct.pack('<3f', *original) != struct.pack('<3f', *reference):
                raise ValueError('original C5/OBJ vertex order differs at mesh %d slot %d' % (mesh, slot))
            mesh_positions.append(struct.pack('<3f', *original))
            for value in original:
                q = round(value * 4096)
                if not -32768 <= q <= 32767:
                    raise ValueError('original XYZ outside signed DS 4.12 range')
                max_error = max(max_error, abs(q / 4096 - value))
        seam_duplicates += sum(n - 1 for n in Counter(mesh_positions).values() if n > 1)
        pos += count
    if max_error > MAX_ERROR:
        raise ValueError('DS coordinate quantization error exceeded')
    return {'ordered_xyz_slots_exact': pos, 'duplicate_xyz_slots_not_uv_verified': seam_duplicates,
            'maximum_xyz_quantization_error': max_error}


def build_pair(c5, obj, model):
    """Verify exact source byte streams, then stage one bounded native pair."""
    from c244_c5_obj_index_provenance import verify as verify_faces, parse_faces
    from c207_private_c5_xyz import convert, obj_vertices
    from c211_private_source_pair import validate_native_pair
    from c5_dual_table_parser import parse

    if type(c5) is not bytes or type(obj) is not bytes:
        raise ValueError('original source inputs must be bounded bytes')
    if len(c5) > 64 * 1024 * 1024 or len(obj) > 64 * 1024 * 1024:
        raise ValueError('private source byte budget exceeded')
    try:
        obj_text = obj.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('reference OBJ is not UTF-8') from exc
    proof = verify_faces(c5, obj_text)
    if not proof['source_face_bytes_exact_and_unique']:
        raise ValueError('original C5 index bytes not independently verified')
    meta = parse(c5)
    first, second = meta['first_table'], meta['second_table']
    vertex_counts = [row['record_count'] for row in first]
    index_counts = [row['low16'] for row in second]
    if len(first) > MAX_MESHES or sum(vertex_counts) > MAX_VERTICES or proof['triangle_count'] > MAX_TRIANGLES:
        raise ValueError('native DS geometry budget exceeded')
    descriptors, vx = convert(c5, obj, model)
    ordered = verify_ordered_xyz(c5, meta, obj_vertices(obj), descriptors)
    _, faces = parse_faces(obj_text)
    ix = pack_index_stream(vertex_counts, index_counts, faces, model)
    native = validate_native_pair(vx, ix, model)
    if (native['vertex_meshes'] != len(first) or native['verified_index_meshes'] != len(first)
            or native['vertices'] != proof['vertex_count'] or native['triangles'] != proof['triangle_count']):
        raise ValueError('native geometry does not reproduce full source partitions')
    return vx, ix, {
        'schema': 'p3d-c245-private-ordered-source-geometry-pair-v1',
        'source_c5_face_bytes_exact_unique': True,
        'source_c5_xyz_order_exact': True,
        'native_p3vx_p3ix_pair_valid': True,
        'source_derived_obj_independently_authenticated': False,
        'original_3ds_renderer_binding_verified': False,
        'original_uv_seam_material_skinning_verified': False,
        'private_asset_emulator_verified': False,
        'full_original_model_verified': False,
        'mesh_count': len(first), 'vertex_count': native['vertices'],
        'triangle_count': native['triangles'], **ordered,
    }


def stage_private(c5_path, obj_path, output_dir):
    """Atomic private directory publication: no partially accepted model pair."""
    from c207_private_c5_xyz import private_path, read_bounded
    from c180_private_c5_coverage import write_private_report
    c5_path, obj_path, output_dir = map(private_path, (c5_path, obj_path, output_dir))
    name = c5_path.stem
    if (len(name) != 4 or name[0] != 'p' or not name[1:].isdigit()
            or obj_path.name != name + '.obj'):
        raise ValueError('source files must share a pNNN identity')
    if output_dir.exists() or output_dir.is_symlink() or not output_dir.parent.is_dir():
        raise ValueError('private output directory must not exist')
    vx, ix, report = build_pair(read_bounded(c5_path), read_bounded(obj_path), int(name[1:]))
    staging = Path(tempfile.mkdtemp(prefix='.c245-', dir=output_dir.parent))
    os.chmod(staging, 0o700)
    try:
        for ext, data in (('p3vx', vx), ('p3ix', ix)):
            path = staging / (name + '.' + ext)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        write_private_report(staging / (name + '.json'), report)
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError('private output appeared during staging')
        os.rename(staging, output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c5', required=True, type=Path)
    parser.add_argument('--obj', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    result = stage_private(args.c5, args.obj, args.output_dir)
    print(json.dumps({'mesh_count': result['mesh_count'],
                      'vertex_count': result['vertex_count'],
                      'triangle_count': result['triangle_count'],
                      'original_renderer_verified': False,
                      'private_emulator_verified': False}, sort_keys=True))


if __name__ == '__main__':
    main()
