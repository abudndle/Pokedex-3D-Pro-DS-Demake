#!/usr/bin/env python3
"""C247: source-backed, explicitly PROVISIONAL C5/OBJ untextured DS geometry.

C244 proves exact original C5 face bytes; this gate proves that every C62
OBJ XYZ exists as an original C5 28-byte-stride float3 record at one unique
alignment residue, with multiplicities. It DOES NOT prove that source record
ownership/order matches the 3DS renderer's indexed vertex buffers. A native
pair produced here is a CANDIDATE, never an authentic completed model.
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
import zlib

from c245_private_ordered_geometry_pair import pack_index_stream

MAX_INPUT = 64 * 1024 * 1024
MAX_VERTICES = 8192
MAX_TRIANGLES = 1800
MAX_MESHES = 64


def global_xyz_source_proof(c5, vertices):
    """Prove unique 28-byte-stride source alignment for ALL OBJ float3 bytes."""
    if type(c5) is not bytes or not 0 < len(c5) <= MAX_INPUT:
        raise ValueError('invalid source C5 byte budget')
    if not 3 <= len(vertices) <= MAX_VERTICES:
        raise ValueError('native vertex budget exceeded')
    packed = []
    max_error = 0.0
    for row in vertices:
        if len(row) != 3 or not all(type(v) in (float, int) and math.isfinite(v) for v in row):
            raise ValueError('invalid source-derived OBJ XYZ')
        for value in row:
            q = round(value * 4096)
            if not -32768 <= q <= 32767:
                raise ValueError('candidate XYZ outside signed DS 4.12 range')
            max_error = max(max_error, abs(q / 4096 - value))
        packed.append(struct.pack('<3f', *row))
    required = Counter(packed)
    residues = []
    # C5 original 28-byte records are four-byte aligned; all seven possible
    # word-aligned residues are checked to reject an arbitrary chosen match.
    for residue in range(0, 28, 4):
        observed = Counter(c5[offset:offset + 12]
                           for offset in range(residue, len(c5) - 11, 28))
        if all(observed[word] >= count for word, count in required.items()):
            residues.append(residue)
    if len(residues) != 1:
        raise ValueError('expected one complete source XYZ stride residue, found %d' % len(residues))
    return {'source_xyz_stride_bytes': 28,
            'source_xyz_alignment_residue_private': residues[0],
            'source_xyz_records_verified': len(vertices),
            'source_xyz_duplicate_slots_uv_unverified': len(vertices) - len(required),
            'maximum_ds_xyz_quantization_error': max_error}


def candidate_pair(c5, obj, model):
    """Make bounded native candidate with explicit unverified binding flags."""
    from c244_c5_obj_index_provenance import verify as verify_faces, parse_faces
    from c207_private_c5_xyz import obj_vertices
    from c5_dual_table_parser import parse
    from c211_private_source_pair import validate_native_pair

    if type(c5) is not bytes or type(obj) is not bytes or len(obj) > MAX_INPUT:
        raise ValueError('invalid private source inputs')
    try:
        text = obj.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('non-UTF8 reference OBJ') from exc
    face_proof = verify_faces(c5, text)
    meta = parse(c5)
    first, second = meta['first_table'], meta['second_table']
    vertex_counts = [row['record_count'] for row in first]
    index_counts = [row['low16'] for row in second]
    vertices = obj_vertices(obj)
    if (not 1 <= len(first) <= MAX_MESHES or sum(vertex_counts) != len(vertices)
            or len(vertices) > MAX_VERTICES or face_proof['triangle_count'] > MAX_TRIANGLES):
        raise ValueError('native DS geometry budget or descriptor count exceeded')
    proof = global_xyz_source_proof(c5, vertices)
    _, faces = parse_faces(text)
    ix = pack_index_stream(vertex_counts, index_counts, faces, model)
    table = bytearray()
    first_vertex = 0
    for mesh, count in enumerate(vertex_counts):
        table += struct.pack('<HHI', mesh, count, first_vertex)
        first_vertex += count
    fixed = [round(value * 4096) for row in vertices for value in row]
    payload = struct.pack('<%dh' % len(fixed), *fixed)
    crc = zlib.crc32(table + payload) & 0xffffffff
    vx = struct.pack('<4sHHHHI', b'P3VX', 1, model, len(first), 0, crc) + table + payload
    native = validate_native_pair(vx, ix, model)
    if native['triangles'] != face_proof['triangle_count'] or native['vertices'] != len(vertices):
        raise ValueError('native candidate differs from source-derived reference')
    return vx, ix, {
        'schema': 'p3d-c247-private-global-xyz-candidate-v1',
        'original_c5_xyz_bytes_present_at_unique_stride': True,
        'original_c5_face_bytes_exact_unique': True,
        'candidate_native_pair_accepted': True,
        'original_3ds_vertex_slot_binding_verified': False,
        'original_uv_seam_material_skinning_verified': False,
        'source_derived_obj_independently_authenticated': False,
        'native_gl_draw_tested': False,
        'asset_integrated_emulator_verified': False,
        'full_original_model_verified': False,
        'mesh_count': len(first), 'vertex_count': len(vertices),
        'triangle_count': native['triangles'], **proof,
    }


def stage_private(c5_path, obj_path, output_dir):
    from c207_private_c5_xyz import private_path, read_bounded
    from c180_private_c5_coverage import write_private_report
    c5_path, obj_path, output_dir = map(private_path, (c5_path, obj_path, output_dir))
    model_name = c5_path.stem
    if (len(model_name) != 4 or model_name[0] != 'p' or not model_name[1:].isdigit()
            or obj_path.name != model_name + '.obj'):
        raise ValueError('private model files must share pNNN identity')
    if output_dir.exists() or output_dir.is_symlink() or not output_dir.parent.is_dir():
        raise ValueError('private output directory must not exist')
    vx, ix, report = candidate_pair(read_bounded(c5_path), read_bounded(obj_path), int(model_name[1:]))
    staging = Path(tempfile.mkdtemp(prefix='.c247-', dir=output_dir.parent))
    os.chmod(staging, 0o700)
    try:
        for extension, data in (('p3vx', vx), ('p3ix', ix)):
            fd = os.open(staging / (model_name + '.' + extension),
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        write_private_report(staging / (model_name + '.json'), report)
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError('private output appeared during staging')
        os.rename(staging, output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c5', type=Path, required=True)
    parser.add_argument('--obj', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = stage_private(args.c5, args.obj, args.output_dir)
    print(json.dumps({'source_xyz_bytes_verified': result['source_xyz_records_verified'],
                      'native_candidate_triangles': result['triangle_count'],
                      'original_renderer_binding_verified': False,
                      'asset_integrated_emulator_verified': False}, sort_keys=True))


if __name__ == '__main__':
    main()
