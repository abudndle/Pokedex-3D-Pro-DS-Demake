"""C172/C213: fail-closed original C5 descriptor and primitive coverage gate.

C5 header 0x10 is NOT the primary mesh descriptor count. The actual primary
and secondary counts are u16 at 0x14 and 0x16, with table offsets at 0x3c.
A matching count is necessary, never independent proof of original topology.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from c171_verified_primitive_gate import verify


def verify_coverage(manifest, source):
    summary = verify(manifest)
    if not isinstance(source, bytes) or len(source) < 0x78 or source[:2] != b'\xc5\x78':
        raise ValueError('invalid original C5 source header')
    primary_count, secondary_count = struct.unpack_from('<2H', source, 0x14)
    vstart, istart, payload_start = struct.unpack_from('<3I', source, 0x3c)
    if (not 1 <= primary_count <= 256 or not 1 <= secondary_count <= 256 or
            not 0x78 <= vstart <= istart <= payload_start <= len(source) or
            istart - vstart != primary_count * 20 or
            payload_start - istart != secondary_count * 12):
        raise ValueError('invalid original C5 descriptor tables')
    model = manifest.get('model')
    if not isinstance(model, str) or len(model) != 4 or model[0] != 'p' or not model[1:].isdigit():
        raise ValueError('invalid model identity')
    if any(row['model'] != model for row in manifest['meshes']):
        raise ValueError('cross-model mapping')
    for row in manifest['meshes']:
        mesh = row['mesh']
        if mesh >= primary_count or mesh >= secondary_count:
            raise ValueError('mesh index outside original descriptor tables')
        vertex_offset, reserved, packed, _, reserved2 = struct.unpack_from(
            '<5I', source, vstart + 20 * mesh)
        vertex_count, vertex_stride = packed & 65535, (packed >> 16) & 255
        if (reserved or reserved2 not in (0, 0x26) or
                not 3 <= vertex_count <= 8192 or vertex_stride < 12 or
                vertex_offset < payload_start or vertex_offset > len(source) or
                vertex_count * vertex_stride > len(source) - vertex_offset):
            raise ValueError('invalid original C5 vertex descriptor')
        index_offset, index_reserved, index_packed = struct.unpack_from(
            '<3I', source, istart + 12 * mesh)
        index_count, index_stride = index_packed & 65535, index_packed >> 16
        if (index_reserved or index_stride == 0 or
                index_offset < payload_start or index_offset > len(source) or
                index_count * index_stride > len(source) - index_offset):
            raise ValueError('invalid original C5 primitive descriptor')
        if index_count % 3 or len(row['triangles']) != index_count // 3:
            raise ValueError('incomplete original triangle coverage')
        if any(i >= vertex_count for tri in row['triangles'] for i in tri):
            raise ValueError('triangle references vertex outside source mesh')
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('private_manifest', type=Path)
    parser.add_argument('private_c5_archive', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.private_manifest.read_text())
    with zipfile.ZipFile(args.private_c5_archive) as archive:
        source = archive.read('decoded_c5/' + manifest['model'] + '.c5')
    print(json.dumps(verify_coverage(manifest, source), sort_keys=True))


if __name__ == '__main__':
    main()
