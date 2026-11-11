#!/usr/bin/env python3
"""C306: synthetic source-indexed and mixed legacy texture previews.
Only authored geometric/color fixtures are staged. No Nintendo assets or
private manifests are read, hashed, copied, or included in public artifacts.
"""
import argparse
import json
import struct
from pathlib import Path
import zlib


def put(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def pack_crc_header(magic, version, model, count_a, count_b, records):
    return (struct.pack("<4sHHHHI", magic, version, model, count_a, count_b,
                        zlib.crc32(records)) + records)


def stage_legacy(destination):
    # Separate triangles let the frame gate distinguish the textured range
    # from the face-color fallback for an out-of-unit UV range.
    xyz = (-2900, -1500, 0, -150, -1500, 0, -1500, 1900, 0,
            150, -1500, 0, 2900, -1500, 0, 1500, 1900, 0)
    put(destination / "preview/p004.ds3m",
        struct.pack("<4sHHII18h6B", b"DS3M", 2, 2, 0, 2, *xyz,
                    255, 255, 255, 235, 20, 30))
    put(destination / "preview/p004.p3uv",
        struct.pack("<4sHH12h", b"P3UV", 1, 2, 0, 0, 4096, 0, 0, 4096,
                    -1, 0, 4096, 0, 0, 4096))
    materials = destination / "materials"
    put(materials / "p004.p3mt",
        struct.pack("<4sHH8H", b"P3MT", 1, 2, 0, 1, 0, 9, 1, 1, 0, 9))
    put(materials / "p004.p3tx",
        struct.pack("<4sHH4H", b"P3TX", 1, 1, 9, 8, 8, 1))
    put(materials / "p004.p3mr", pack_crc_header(
        b"P3MR", 1, 4, 2, 1, struct.pack("<6H", 0, 2, 0, 9, 0xffff, 0x0c02)))
    put(materials / "p004.p3sc", pack_crc_header(
        b"P3SC", 2, 4, 1, 0, struct.pack("<5H", 0, 0, 9, 0xffff, 1)))
    put(materials / "p004.p3sw", pack_crc_header(
        b"P3SW", 1, 4, 1, 0, struct.pack("<13I", 0, 0xffff0009, *([0] * 11))))
    put(destination / "textures/p004/t009.p3px",
        struct.pack("<4sHHH64H", b"P3PX", 2, 8, 8, *([0x83e0] * 64)))


def stage_mixed_native(destination):
    mesh = struct.pack("<HHI", 0, 6, 0)
    xyz = (destination / "preview/p004.ds3m").read_bytes()[16:52]
    geometry = destination / "geometry"
    vx = pack_crc_header(b"P3VX", 1, 5, 1, 0, mesh + xyz)
    put(geometry / "p005.p3vx", vx)
    put(geometry / "p005.p3ix", struct.pack("<4sHHHHI6H", b"P3IX", 1, 5, 1, 0, 2, *range(6)))
    uv = mesh + struct.pack("<12h", *([0, 0, 4096, 0, 0, 4096] * 2))
    put(geometry / "p005.p3vu", struct.pack("<4sHHHHII", b"P3VU", 1, 5, 1, 0,
        zlib.crc32(vx), zlib.crc32(uv)) + uv)
    materials = destination / "materials"
    put(materials / "p005.p3mt", struct.pack("<4sHH8H", b"P3MT", 1, 2,
        0, 1, 0, 9, 1, 1, 1, 10))
    put(materials / "p005.p3tx", struct.pack("<4sHH8H", b"P3TX", 1, 2,
        9, 8, 8, 1, 10, 8, 8, 1))
    source = struct.pack("<12H", 0, 1, 0, 9, 0xffff, 0x0c02,
                         1, 1, 1, 10, 0xffff, 0x0c02)
    put(materials / "p005.p3mr", pack_crc_header(b"P3MR", 1, 5, 2, 2, source))
    caps = struct.pack("<10H", 0, 0, 9, 0xffff, 1, 1, 1, 10, 0xffff, 2)
    put(materials / "p005.p3sc", pack_crc_header(b"P3SC", 2, 5, 2, 0, caps))
    words = b"".join(struct.pack("<13I", shader, 0xffff0000 | texture, *([0] * 11))
                     for shader, texture in ((0, 9), (1, 10)))
    put(materials / "p005.p3sw", pack_crc_header(b"P3SW", 1, 5, 2, 0, words))
    # Deliberately omit the unsupported material's texture payload.
    put(destination / "textures/p005/t009.p3px",
        (destination / "textures/p004/t009.p3px").read_bytes())


def stage(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or list(root.iterdir()):
        raise ValueError("requires a new, empty, non-symlinked temp directory")
    destination = root / "staged"
    try:
        mapping = [0xffff] * 649
        mapping[:4] = [2, 3, 4, 5]
        put(destination / "models/species_map.p3sm",
            struct.pack("<4sHH649H", b"P3SM", 1, 649, *mapping))
        for model, tex_id, color in ((2, 7, 0x801f), (3, 8, 0xfc00)):
            mesh = struct.pack("<HHI", 0, 3, 0)
            coords = struct.pack("<9h", 0, 0, 0, 4096, 0, 0, 0, 4096, 0)
            vx = struct.pack("<4sHHHHI", b"P3VX", 1, model, 1, 0,
                             zlib.crc32(mesh + coords)) + mesh + coords
            ix = struct.pack("<4sHHH", b"P3IX", 1, model, 1)
            ix += struct.pack("<HI3H", 0, 1, 0, 1, 2)
            uv_table = struct.pack("<HHI", 0, 3, 0)
            uv_values = struct.pack("<6h", 0, 0, 4096, 0, 0, 4096)
            vu_payload = uv_table + uv_values
            vu = struct.pack("<4sHHHHII", b"P3VU", 1, model, 1, 0,
                             zlib.crc32(vx), zlib.crc32(vu_payload)) + vu_payload
            stem = f"p{model:03d}"
            put(destination / "geometry" / (stem + ".p3vx"), vx)
            put(destination / "geometry" / (stem + ".p3ix"), ix)
            put(destination / "geometry" / (stem + ".p3vu"), vu)
            put(destination / "materials" / (stem + ".p3mt"),
                struct.pack("<4sHH4H", b"P3MT", 1, 1, 0, 1, 0, tex_id))
            put(destination / "materials" / (stem + ".p3tx"),
                struct.pack("<4sHH4H", b"P3TX", 1, 1, tex_id, 8, 8, 1))
            source = struct.pack("<6H", 0, 1, 0, tex_id, 0xffff, 0x0c02)
            put(destination / "materials" / (stem + ".p3mr"),
                pack_crc_header(b"P3MR", 1, model, 1, 1, source))
            cap = struct.pack("<5H", 0, 0, tex_id, 0xffff, 1)
            put(destination / "materials" / (stem + ".p3sc"),
                pack_crc_header(b"P3SC", 2, model, 1, 0, cap))
            words = struct.pack("<13I", 0, (0xffff << 16) | tex_id,
                                *([0] * 11))
            put(destination / "materials" / (stem + ".p3sw"),
                pack_crc_header(b"P3SW", 1, model, 1, 0, words))
            put(destination / "textures" / stem / f"t{tex_id:03d}.p3px",
                struct.pack("<4sHHH", b"P3PX", 2, 8, 8) +
                struct.pack("<64H", *([color] * 64)))
        stage_legacy(destination)
        stage_mixed_native(destination)
        return destination
    except Exception:
        # A failed synthetic stage must not leave partially usable private-
        # looking files. The entire temporary root is owned by its CI caller.
        import shutil
        shutil.rmtree(destination, ignore_errors=True)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("empty_temp_dir", type=Path)
    args = p.parse_args()
    output = stage(args.empty_temp_dir)
    print(json.dumps({"schema": "c306-synthetic-texture-visual-v1",
                      "staged": str(output), "models": [2, 3, 4, 5],
                      "synthetic_texture_colors": ["red", "blue", "green"],
                      "nintendo_assets_included": False,
                      "original_visual_parity_verified": False}, sort_keys=True))
