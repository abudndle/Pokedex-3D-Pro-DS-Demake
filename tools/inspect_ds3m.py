#!/usr/bin/env python3
"""Inspect locally supplied DS3M previews without uploading proprietary assets.

Format contract used by the runtime:
  16-byte header: magic DS3M, u16 version, u16 triangle count,
  u32 reserved, u32 original triangle count.
  Triangle XYZ: 9 signed little-endian 16-bit coordinates per triangle.
  v2 additionally contains 3 RGB888 bytes per triangle, after all XYZ.
These checks validate the proposed decoder contract, NOT original-file provenance.
"""
import argparse
from pathlib import Path
import struct
import sys

HEADER = struct.Struct("<4sHHII")
MAX_TRIANGLES = 600

def inspect(path: Path):
    with path.open("rb") as stream:
        header = stream.read(HEADER.size)
        if len(header) != HEADER.size:
            raise ValueError("truncated DS3M header")
        magic, version, triangles, reserved, original = HEADER.unpack(header)
        if magic != b"DS3M" or version not in (1, 2):
            raise ValueError("unsupported DS3M magic or version")
        if reserved != 0:
            raise ValueError("DS3M reserved header field must be zero")
        if not 1 <= triangles <= MAX_TRIANGLES:
            raise ValueError("triangle count outside DS preview budget")
        expected = HEADER.size + triangles * 18 + (triangles * 3 if version == 2 else 0)
        size = path.stat().st_size
        if size != expected:
            raise ValueError(f"incorrect byte length: expected {expected}, got {size}")
        # Match loader semantics; do not assume original triangles are present.
        return {"version": version, "triangles": triangles, "original": original, "bytes": size}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        try:
            result = inspect(path)
            print(f"PASS {path}: {result}")
        except (OSError, ValueError) as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            failed = True
    return int(failed)

if __name__ == "__main__":
    raise SystemExit(main())
