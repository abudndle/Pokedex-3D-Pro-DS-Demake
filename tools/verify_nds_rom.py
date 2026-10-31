#!/usr/bin/env python3
"""Structural sanity check for an NDS ROM emitted by ndstool.

This does not emulate or prove the game is playable.
"""
import argparse
from pathlib import Path
import struct
import sys

def verify(path: Path):
    data = path.read_bytes()
    if len(data) < 0x200:
        return ["NDS image is smaller than the 512-byte minimum header"]
    errors = []
    for name, offset_at in (("ARM9", 0x20), ("ARM7", 0x30)):
        offset, entry, ram, size = struct.unpack_from("<IIII", data, offset_at)
        if offset < 0x200 or size == 0 or offset + size > len(data):
            errors.append(f"{name} data points outside ROM or has zero size")
        if not entry or not ram:
            errors.append(f"{name} has no entry point or RAM destination")
        if offset & 3:
            errors.append(f"{name} offset is not word-aligned")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()
    try:
        problems = verify(args.rom)
    except OSError as exc:
        print(f"Cannot read ROM: {exc}", file=sys.stderr)
        return 1
    for item in problems:
        print(f"ERROR: {item}", file=sys.stderr)
    if problems:
        return 1
    print(f"NDS ARM9/ARM7 header checks: PASS ({args.rom})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
