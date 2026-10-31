#!/usr/bin/env python3
"""Sanity-check the structure of a generated DS cartridge image.

This is not an emulator boot test. It catches empty, truncated, or malformed
ARM9/ARM7 packaging in the native smoke ROM build.
"""
from pathlib import Path
import struct
import sys


def verify(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 0x200:
        raise ValueError("ROM is smaller than the 512-byte NDS header")
    for cpu, offset in (("ARM9", 0x20), ("ARM7", 0x30)):
        rom_start, entry, ram_start, length = struct.unpack_from("<4I", data, offset)
        if length == 0:
            raise ValueError(f"{cpu} section is empty")
        if rom_start < 0x200 or rom_start > len(data):
            raise ValueError(f"{cpu} ROM offset is outside the image")
        if length > len(data) - rom_start:
            raise ValueError(f"{cpu} section overruns the image")
        if entry == 0 or ram_start == 0:
            raise ValueError(f"{cpu} entry or RAM address is zero")
        print(f"{cpu}: ROM 0x{rom_start:X}, {length} bytes; entry 0x{entry:X}")
    print(f"NDS header and ARM sections: OK ({len(data)} bytes)")


if __name__ == "__main__":
    try:
        verify(Path(sys.argv[1]))
    except (IndexError, OSError, ValueError) as exc:
        sys.exit(f"NDS validation failed: {exc}")
