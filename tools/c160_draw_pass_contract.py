#!/usr/bin/env python3
"""C160: fail-closed original C5 draw-pass contract; no private assets bundled."""
import struct

PRIMARY = 0x0c02
SECONDARY = 0x0c01

def parse_draws(raw):
    if len(raw) < 120 or raw[:2] != b"\xc5x":
        raise ValueError("invalid original C5 header")
    materials = struct.unpack_from("<H", raw, 0x10)[0]
    meshes, indices = struct.unpack_from("<2H", raw, 0x14)
    count = struct.unpack_from("<H", raw, 0x18)[0]
    vertices_at, indices_at, draws_at = struct.unpack_from("<3I", raw, 0x3c)
    draws_end = struct.unpack_from("<I", raw, 0x50)[0]
    if not (0 < materials <= 256 and 0 < meshes == indices <= 1000
            and 0 < count <= 1024 and vertices_at >= 120
            and indices_at == vertices_at + 20 * meshes
            and draws_at == indices_at + 12 * indices
            and draws_end == draws_at + 40 * count
            and draws_end <= len(raw)):
        raise ValueError("invalid original C5 table boundaries")
    rows = []
    for i in range(count):
        packed, vertex, index, _, faces, _, _, mode = struct.unpack_from(
            "<8H", raw, draws_at + 40 * i)
        material = packed & 255
        if mode not in (PRIMARY, SECONDARY):
            raise ValueError("unsupported original draw pass")
        if not (material < materials and vertex == index < meshes and faces > 0):
            raise ValueError("invalid original draw reference")
        index_count = struct.unpack_from("<I", raw, indices_at + index * 12 + 8)[0] & 65535
        if faces * 3 != index_count:
            raise ValueError("original draw face count mismatch")
        rows.append((i, vertex, material, mode, faces))
    return meshes, rows

def classify_meshes(mesh_count, rows):
    """Do not invent a primary material for secondary-only meshes."""
    result = []
    for mesh in range(mesh_count):
        primary = sorted({r[2] for r in rows if r[1] == mesh and r[3] == PRIMARY})
        secondary = sorted({r[2] for r in rows if r[1] == mesh and r[3] == SECONDARY})
        if not primary and not secondary:
            raise ValueError("mesh has no source draw")
        result.append({
            "mesh": mesh,
            "primary_material": primary[0] if len(primary) == 1 else None,
            "secondary_materials": secondary,
            "primary_verified": len(primary) == 1,
            "sampler_roles_verified": False,
        })
        if len(primary) > 1:
            raise ValueError("ambiguous primary material")
    return result
