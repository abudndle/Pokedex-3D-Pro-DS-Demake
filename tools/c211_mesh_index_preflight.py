#!/usr/bin/env python3
"""Fail-closed mesh-local index preflight for private P3VX/P3IX sidecars.

The native C pair loader remains the authority; this mirrors its per-mesh
index bound check and never exposes private geometry in output.
"""
import struct
import zlib

MAX_VERTEX_BYTES = 16 + 64 * 8 + 8192 * 6
MAX_INDEX_BYTES = 10 + 64 * 6 + 1800 * 6
from pathlib import Path

def inspect_pair(vertex_path, index_path, model):
    if Path(vertex_path).stat().st_size > MAX_VERTEX_BYTES:
        raise ValueError("oversized vertex stream")
    if Path(index_path).stat().st_size > MAX_INDEX_BYTES:
        raise ValueError("oversized index stream")
    vx = Path(vertex_path).read_bytes()
    ix = Path(index_path).read_bytes()
    if len(vx) < 24 or vx[:4] != b"P3VX":
        raise ValueError("invalid vertex header")
    version, found, count, reserved, crc = struct.unpack_from("<HHHHI", vx, 4)
    if version != 1 or found != model or reserved or not 1 <= count <= 64:
        raise ValueError("invalid vertex identity")
    table_end = 16 + 8 * count
    if table_end > len(vx) or zlib.crc32(vx[16:]) != crc:
        raise ValueError("invalid vertex table or CRC")
    vertices = {}
    first_expected = 0
    for offset in range(16, table_end, 8):
        mesh, size, first = struct.unpack_from("<HHI", vx, offset)
        if mesh >= 64 or mesh in vertices or (vertices and mesh <= max(vertices)):
            raise ValueError("invalid vertex mesh order")
        if size < 3 or first != first_expected or size > 8192 - first_expected:
            raise ValueError("invalid vertex mesh extent")
        vertices[mesh] = size
        first_expected += size
    if len(vx) != table_end + first_expected * 6:
        raise ValueError("invalid vertex payload length")
    if len(ix) < 16 or ix[:4] != b"P3IX":
        raise ValueError("invalid index header")
    ix_version, ix_model, ix_count = struct.unpack_from("<HHH", ix, 4)
    if ix_version != 1 or ix_model != model or not 1 <= ix_count <= 64:
        raise ValueError("invalid index identity")
    pos, triangles, previous = 10, 0, -1
    index_meshes = []
    for _ in range(ix_count):
        if pos + 6 > len(ix):
            raise ValueError("truncated index mesh")
        mesh, count = struct.unpack_from("<HI", ix, pos)
        pos += 6
        if mesh <= previous or mesh not in vertices or not count or count > 1800 - triangles:
            raise ValueError("invalid index mesh")
        previous = mesh
        index_meshes.append(mesh)
        size = count * 6
        if size > len(ix) - pos:
            raise ValueError("truncated index payload")
        for offset in range(pos, pos + size, 6):
            a, b, c = struct.unpack_from("<HHH", ix, offset)
            if max(a, b, c) >= vertices[mesh]:
                raise ValueError("index exceeds mesh-local vertex count")
            if len({a, b, c}) != 3:
                raise ValueError("degenerate triangle")
        pos += size
        triangles += count
    if index_meshes != list(vertices):
        raise ValueError("index and vertex mesh rosters differ")
    if pos != len(ix):
        raise ValueError("trailing index bytes")
    return triangles
