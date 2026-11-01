#!/usr/bin/env python3
"""Prepare privately recovered 256x192 UI pages for NitroFS; never distribute source assets."""
import argparse
import pathlib
import struct
import sys

NAMES = ("home", "dex", "search", "moves", "types", "favorites", "challenge",
         "settings", "album", "ar", "records")
PIXELS = 256 * 192
SIZE = PIXELS * 2

def convert(src: pathlib.Path, dst: pathlib.Path) -> None:
    data = src.read_bytes()
    if len(data) == SIZE:
        out = data
    elif len(data) == PIXELS * 4:
        # Explicit RGBA8888 input, row-major top-to-bottom. DS bit15 enables pixels.
        values = bytearray(SIZE)
        for i in range(PIXELS):
            r, g, b, a = data[4*i:4*i+4]
            rgb = (0x8000 if a else 0) | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)
            struct.pack_into("<H", values, 2*i, rgb)
        out = bytes(values)
    else:
        raise ValueError(f"{src}: expected {SIZE} RGB555 or {PIXELS*4} RGBA bytes, got {len(data)}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(out)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=pathlib.Path, help="Private folder with PAGE_NAME.rgb555 or .rgba")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("nitrofs/ui/pages"))
    args = parser.parse_args()
    count = 0
    for page, name in enumerate(NAMES):
        for ext in (".rgb555", ".rgba"):
            source = args.source / f"{name}{ext}"
            if source.is_file():
                destination = args.output / f"t0_{page:02d}_{name}.rgb555"
                convert(source, destination)
                print(f"{source} -> {destination}")
                count += 1
                break
    if not count:
        print("No recognized private UI pages supplied; ROM will use text fallback.", file=sys.stderr)
        return 1
    print(f"Prepared {count}/{len(NAMES)} UI pages (private build only).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
