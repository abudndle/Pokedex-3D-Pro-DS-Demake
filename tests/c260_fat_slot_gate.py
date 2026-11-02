#!/usr/bin/env python3
"""C260: validate *synthetic* native P3SV/P3RV FAT exports, not private data."""
import argparse
from pathlib import Path
import struct
import zlib


def valid_slots(root: Path, stem: str, magic: bytes, size: int, crc_at: int):
    valid = []
    for slot in "AB":
        target = (stem + "_" + slot + ".sav").lower()
        paths = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == target]
        if len(paths) > 1:
            raise ValueError("ambiguous exported slot: " + target)
        if not paths:
            continue
        data = paths[0].read_bytes()
        if len(data) != size or data[:4] != magic:
            continue
        if struct.unpack_from("<I", data, crc_at)[0] != zlib.crc32(data[:crc_at]):
            continue
        valid.append((struct.unpack_from("<I", data, 8)[0], data))
    if not valid:
        raise ValueError("no valid " + magic.decode() + " FAT slot")
    return max(valid, key=lambda item: item[0])[1]


def check(root: Path):
    if not root.is_dir():
        raise ValueError("missing FAT export directory")
    save = valid_slots(root, "pokedex3d", b"P3SV", 64, 60)
    resume = valid_slots(root, "pokedex3d_resume", b"P3RV", 80, 76)
    if save[4] != 1 or save[16] != 1 or struct.unpack_from("<H", save, 20)[0] != 0:
        raise ValueError("favorite not committed to native save")
    if resume[4] != 3 or resume[12] != 0 or resume[13] != 1:
        raise ValueError("Dex page not committed to native resume")
    if struct.unpack_from("<H", resume, 16)[0] != 0:
        raise ValueError("unexpected resumed species")
    return {"p3sv_crc": "valid", "p3rv_crc": "valid", "favorite_000": True,
            "resume_dex_000": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("export_root", type=Path)
    print("C260 FAT export gate:", check(p.parse_args().export_root))
