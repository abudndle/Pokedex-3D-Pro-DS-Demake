#!/usr/bin/env python3
"""Convert a uniquely source-matched private C5 float3 stream to P3VX v1.

An OBJ is used only as independent XYZ ordering evidence. Neither OBJ faces nor
original C5 topology/material/skin data is inferred. Run only on authorized
private files; no original data, output, or hashes belong in public GitHub.
"""
import argparse
import math
import os
from pathlib import Path
import re
import struct
import zlib

MODEL = re.compile(r"p([0-9]{3})\Z")
MAX_INPUT = 64 * 1024 * 1024
MAX_VERTICES = 8192
REPO = Path(__file__).resolve().parents[1]


def private_path(value):
    path = Path(value).expanduser().absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('symlinked private path')
    resolved = path.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError('private input and output must be outside public repository')
    return resolved


def read_bounded(path):
    path = private_path(path)
    if not path.is_file() or path.stat().st_size > MAX_INPUT:
        raise ValueError('missing or oversized private input')
    with path.open('rb') as stream:
        data = stream.read(MAX_INPUT + 1)
    if len(data) > MAX_INPUT:
        raise ValueError('oversized private input')
    return data


def c5_candidates(data):
    if len(data) < 0x78 or data[:2] != b'\xc5\x78':
        raise ValueError('invalid C5 header')
    a, b, c = struct.unpack_from('<3I', data, 0x3c)
    n1, n2 = struct.unpack_from('<2H', data, 0x14)
    if not (0x78 <= a <= b <= c <= len(data)) or b-a != n1*20 or c-b != n2*12:
        raise ValueError('invalid C5 descriptor bounds')
    candidates = []
    for i in range(n1):
        off, reserved, packed, layout, reserved2 = struct.unpack_from('<5I', data, a+i*20)
        count, stride = packed & 65535, (packed >> 16) & 255
        if reserved or reserved2 not in (0, 0x26) or off < c or off > len(data) or count*stride > len(data)-off:
            raise ValueError('invalid C5 primary descriptor')
        if stride != 28 or not 3 <= count <= MAX_VERTICES:
            continue
        xyz = [struct.unpack_from('<3f', data, off+j*stride) for j in range(count)]
        if all(math.isfinite(v) for vertex in xyz for v in vertex):
            candidates.append((i, xyz))
    for i in range(n2):
        off, reserved, packed = struct.unpack_from('<3I', data, b+i*12)
        count, stride = packed & 65535, packed >> 16
        if reserved or off > len(data) or count*stride > len(data)-off:
            raise ValueError('invalid C5 secondary descriptor')
    return candidates


def obj_vertices(data):
    vertices = []
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('non-UTF8 reference OBJ') from exc
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0] != 'v':
            continue
        if len(parts) not in (4, 5):
            raise ValueError('malformed OBJ vertex')
        try:
            xyz = tuple(float(part) for part in parts[1:4])
        except ValueError as exc:
            raise ValueError('invalid OBJ vertex') from exc
        if not all(math.isfinite(v) for v in xyz):
            raise ValueError('nonfinite OBJ vertex')
        vertices.append(xyz)
        if len(vertices) > MAX_VERTICES:
            raise ValueError('OBJ vertex budget exceeded')
    if len(vertices) < 3:
        raise ValueError('too few OBJ vertices')
    return vertices


def convert(c5, obj, model):
    if type(model) is not int or model not in (set(range(734))-{721,722,723,724}):
        raise ValueError('invalid model ID')
    reference = obj_vertices(obj)
    matches = [(idx, xyz) for idx, xyz in c5_candidates(c5)
               if len(xyz) == len(reference) and
               all(abs(a-b) <= 1e-6 for source, expected in zip(xyz, reference)
                   for a,b in zip(source, expected))]
    if len(matches) != 1:
        raise ValueError('C5 XYZ source match must be unique (found %d)' % len(matches))
    descriptor, xyz = matches[0]
    fixed = []
    for vertex in xyz:
        for value in vertex:
            q = round(value*4096)
            if not -32768 <= q <= 32767:
                raise ValueError('source coordinate outside DS signed 4.12 range')
            fixed.append(q)
    table = struct.pack('<HHI', 0, len(xyz), 0)
    payload = struct.pack('<%dh' % len(fixed), *fixed)
    crc = zlib.crc32(table+payload) & 0xffffffff
    output = struct.pack('<4sHHHHI', b'P3VX', 1, model, 1, 0, crc)+table+payload
    return descriptor, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c5', required=True, type=Path)
    parser.add_argument('--obj', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    c5, obj, target = map(private_path, (args.c5, args.obj, args.output))
    match = MODEL.fullmatch(c5.stem)
    if match is None or obj.stem != c5.stem or target.name != c5.stem+'.p3vx':
        parser.error('private files must use matching pNNN names')
    descriptor, result = convert(read_bounded(c5), read_bounded(obj), int(match.group(1)))
    if not target.parent.is_dir():
        parser.error('private output directory must exist')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(result)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    print('P3VX model', match.group(1), 'source descriptor', descriptor,
          'vertices', (len(result)-24)//6, '(topology, materials, animation NOT verified)')


if __name__ == '__main__':
    main()
