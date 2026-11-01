#!/usr/bin/env python3
"""Prepare private 3DS top and bottom UI pages for DS NitroFS; never distribute assets."""
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
    # Legacy root files are the original bottom-screen pages. Top-screen art
    # must be provided independently; do not duplicate or fabricate pages.
    # Accept either <source>/top/<name> or <source>/top_<name> for the top.
    for screen in (0, 1):
        for page, name in enumerate(NAMES):
            for ext in (".rgb555", ".rgba"):
                candidates = (
                    (args.source / f"{name}{ext}",) if screen == 0 else
                    (args.source / "top" / f"{name}{ext}",
                     args.source / f"top_{name}{ext}")
                )
                source = next((path for path in candidates if path.is_file()), None)
                if source is not None:
                    destination = args.output / f"t{screen}_{page:02d}_{name}.rgb555"
                    convert(source, destination)
                    print(f"{source} -> {destination}")
                    count += 1
                    break
    # The original title is NOT the home menu. Require two independently
    # recovered 3DS title frames; missing either refuses to fabricate one.
    title_sources = []
    for screen in (0, 1):
        candidates = []
        for ext in (".rgb555", ".rgba"):
            if screen == 0:
                candidates.extend((args.source / f"title{ext}",
                                   args.source / "bottom" / f"title{ext}"))
            else:
                candidates.extend((args.source / "top" / f"title{ext}",
                                   args.source / f"top_title{ext}"))
        title_sources.append(next((p for p in candidates if p.is_file()), None))
    if any(title_sources):
        if not all(title_sources):
            raise ValueError("original 3DS title needs both independent top and bottom source frames")
        for screen, source in enumerate(title_sources):
            destination = args.output.parent / "title" / f"t{screen}_title.rgb555"
            convert(source, destination)
            print(f"{source} -> {destination}")
            count += 1
    # An original masked HUD is distinct from the full upper Dex page.
    # Preserve the source alpha bit: clear pixels reveal native BG0 3D.
    # Do not fabricate transparency by guessing at original artwork.
    for page, name in enumerate(NAMES):
        for ext in (".rgb555", ".rgba"):
            candidates = (args.source / "top" / f"{name}_overlay{ext}",
                          args.source / f"top_{name}_overlay{ext}")
            source = next((path for path in candidates if path.is_file()), None)
            if source is None:
                continue
            destination = args.output / f"t1_{page:02d}_{name}_overlay.rgb555"
            data = source.read_bytes()
            if len(data) == SIZE:
                values = data
            elif len(data) == PIXELS * 4:
                values = bytearray(SIZE)
                for i in range(PIXELS):
                    r, g, b, a = data[4*i:4*i+4]
                    pixel = (0x8000 if a else 0) | ((b>>3)<<10) | ((g>>3)<<5) | (r>>3)
                    struct.pack_into("<H",values,i*2,pixel)
            else:
                raise ValueError(f"{source}: invalid transparent UI overlay size")
            # Both an opaque original HUD region and a transparent model
            # viewport are required; this is a binary A1 mask, not ARGB.
            visible = any(values[j+1]&0x80 for j in range(0,SIZE,2))
            cutout = any(not(values[j+1]&0x80) for j in range(0,SIZE,2))
            if not (visible and cutout):
                raise ValueError(f"{source}: original overlay requires opaque UI and transparent 3D cutout")
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(values)
            print(f"{source} -> {destination}")
            count += 1
            break
    if not count:
        print("No original UI/title pages supplied; development ROM will use text fallback.", file=sys.stderr)
        return 1
    print(f"Prepared {count} private UI images ({2*len(NAMES)} independent full-screen pages plus optional source masks).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
