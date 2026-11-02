#!/usr/bin/env python3
"""C244: private exact C5 index-stream vs C62 OBJ byte provenance gate.

This proves an OBJ face stream is present in a decoded C5 source file after
per-mesh local index rebasing and 4-byte alignment. The OBJ is source-derived;
this is NOT an independent original GPU draw trace or material/UV proof.
"""
import argparse
from pathlib import Path
import struct

from c5_dual_table_parser import parse
from c180_private_c5_coverage import write_private_report

MAX_INPUT = 64 * 1024 * 1024
MAX_MESHES = 64
MAX_VERTICES = 200000
MAX_TRIANGLES = 500000
MAX_CANDIDATES = 4096
ROOT = Path(__file__).resolve().parents[1]


def parse_faces(text):
    vertices = 0
    faces = []
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        if parts[0] == 'v':
            if len(parts) != 4:
                raise ValueError('OBJ vertex must contain XYZ')
            vertices += 1
            if vertices > MAX_VERTICES:
                raise ValueError('OBJ vertex budget exceeded')
        elif parts[0] == 'f':
            if len(parts) != 4:
                raise ValueError('OBJ must contain only triangles')
            face = []
            for token in parts[1:]:
                idx = token.split('/')[0]
                if not idx.isdecimal() or int(idx) < 1:
                    raise ValueError('OBJ face must use positive vertex indices')
                face.append(int(idx) - 1)
            faces.append(face)
            if len(faces) > MAX_TRIANGLES:
                raise ValueError('OBJ triangle budget exceeded')
    if not 3 <= vertices <= MAX_VERTICES or not faces:
        raise ValueError('empty OBJ geometry')
    if any(index >= vertices for face in faces for index in face):
        raise ValueError('OBJ face outside vertex roster')
    return vertices, faces


def verify(c5, obj_text):
    if not isinstance(c5, bytes) or not 0x78 <= len(c5) <= MAX_INPUT:
        raise ValueError('invalid C5 byte budget')
    if not isinstance(obj_text, str) or len(obj_text.encode('utf-8')) > MAX_INPUT:
        raise ValueError('invalid OBJ byte budget')
    meta = parse(c5)
    if not meta['structural_checks_passed']:
        raise ValueError('C5 descriptor bounds failed')
    first, second = meta['first_table'], meta['second_table']
    if not 1 <= len(first) == len(second) <= MAX_MESHES:
        raise ValueError('C5 mesh table mismatch')
    vertices, faces = parse_faces(obj_text)
    vcounts = [r['record_count'] for r in first]
    icounts = [r['low16'] for r in second]
    if (sum(vcounts) != vertices or any(not 3 <= count <= 65535 for count in vcounts)
            or any(r['high16'] != 2 or count < 3 or count % 3
                   for r, count in zip(second, icounts))
            or sum(icounts) != 3 * len(faces)):
        raise ValueError('C5/OBJ descriptor vertex or triangle counts differ')
    groups = []
    base = face_index = 0
    for vertex_count, index_count in zip(vcounts, icounts):
        local = []
        for face in faces[face_index:face_index + index_count // 3]:
            for value in face:
                index = value - base
                if not 0 <= index < vertex_count:
                    raise ValueError('OBJ face crosses C5 mesh partition')
                local.append(index)
        groups.append(struct.pack('<' + str(len(local)) + 'H', *local))
        base += vertex_count
        face_index += index_count // 3
    if face_index != len(faces):
        raise ValueError('incomplete OBJ face coverage')

    anchor = groups[0]
    found = []
    at = c5.find(anchor)
    candidates = 0
    while at >= 0:
        candidates += 1
        if candidates > MAX_CANDIDATES:
            raise ValueError('C5 anchor ambiguity budget exceeded')
        if at % 4 == 0:
            position = at
            nonzero_padding = 0
            for group in groups:
                end = position + len(group)
                if end > len(c5) or c5[position:end] != group:
                    break
                aligned = (end + 3) & ~3
                if aligned > len(c5):
                    break
                nonzero_padding += bool(any(c5[end:aligned]))
                position = aligned
            else:
                found.append((at, nonzero_padding))
                if len(found) > 1:
                    raise ValueError('ambiguous C5 source face-stream regions')
        at = c5.find(anchor, at + 1)
    if len(found) != 1:
        raise ValueError('no unique aligned C5 source face-stream region')
    return {
        'schema': 'p3d-c244-private-c5-obj-face-byte-provenance-v1',
        'source_face_bytes_exact_and_unique': True,
        'original_renderer_primitive_binding_verified': False,
        'reference_independently_authenticated': False,
        'original_uv_material_skinning_verified': False,
        'native_ds_rendering_verified': False,
        'mesh_count': len(groups), 'vertex_count': vertices,
        'triangle_count': len(faces),
        'nonzero_alignment_gaps': found[0][1],
        'source_offset_private': found[0][0],
    }


def private_file(path):
    original = Path(path).expanduser()
    if original.is_symlink():
        raise ValueError('private source symlink refused')
    resolved = original.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError('private source must remain outside public repo')
    if not resolved.is_file() or resolved.stat().st_size > MAX_INPUT:
        raise ValueError('private source missing or oversized')
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c5', type=Path, required=True)
    parser.add_argument('--obj', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    c5 = private_file(args.c5).read_bytes()
    obj = private_file(args.obj).read_text(encoding='utf-8')
    result = verify(c5, obj)
    write_private_report(args.report, result)
    print('C244 source face bytes verified for', result['mesh_count'],
          'meshes,', result['triangle_count'],
          'triangles; original renderer binding verified: False')


if __name__ == '__main__':
    main()
