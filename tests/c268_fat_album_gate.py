#!/usr/bin/env python3
"""C268: fail-closed host FAT Album roster gate; not proof of emulator UI."""
import argparse
from pathlib import Path
import re

PHOTO = re.compile(r"AR_[0-9]{4}\.png\Z")


def check(root: Path, expected: tuple[str, ...]) -> dict:
    folder = root / "Pokedex 3D Pro" / "Photos"
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("native FAT Album folder missing or symlinked")
    found = []
    for entry in folder.iterdir():
        if entry.is_symlink():
            raise ValueError("symlinked Album entry")
        if entry.name.startswith("AR_") and not PHOTO.fullmatch(entry.name):
            raise ValueError("malformed Album photo name")
        if PHOTO.fullmatch(entry.name):
            if not entry.is_file():
                raise ValueError("Album photo name is not a file")
            found.append(entry.name)
    found.sort()
    if found != sorted(expected):
        raise ValueError(f"native FAT Album roster mismatch: {len(found)} files")
    return {"photos": len(found), "newest": found[-1] if found else None,
            "fat_folder_verified": True, "emulator_ui_verified": False,
            "dsi_camera_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("export_root", type=Path)
    parser.add_argument("--after-delete", action="store_true")
    args = parser.parse_args()
    count = 8 if args.after_delete else 9
    print("C268 synthetic FAT Album roster:", check(
        args.export_root, tuple(f"AR_{i:04d}.png" for i in range(1, count + 1))))
