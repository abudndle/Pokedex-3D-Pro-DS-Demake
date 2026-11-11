#!/usr/bin/env python3
"""C306: real emulator XWD visual gate for independently authored textures.
This verifies authored source-indexed colors and mixed legacy material
rendering. Original asset fidelity requires separate evidence.
"""
import json
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c235_emulator_frame_gate import read_xwd, compare_frames


def frame_rgb(path):
    raw = Path(path).read_bytes()
    fields = struct.unpack_from(">25I", raw)
    mask = fields[14:17]
    if any(m == 0 for m in mask) or any(m & (m + (m & -m)) for m in mask):
        raise ValueError("XWD lacks contiguous RGB masks")
    shape, pixels = read_xwd(path)
    width, height, stride, size = shape
    order = "little" if fields[7] == 0 else "big" if fields[7] == 1 else None
    if order is None:
        raise ValueError("invalid XWD byte order")

    def rgba(x, y):
        offset = y * stride + x * size
        value = int.from_bytes(pixels[offset:offset + size], order)
        components = []
        for m in mask:
            shift = (m & -m).bit_length() - 1
            n = (value & m) >> shift
            maximum = m >> shift
            components.append((n * 255 + maximum // 2) // maximum)
        return tuple(components)
    return width, height, rgba


def count_dominant(frame, index, bounds=(55, 65, 215, 175)):
    width, height, color = frame
    x0, y0, x1, y1 = bounds
    if width != 256 or height != 384:
        raise ValueError("expected 256x384 dual-screen native frame")
    other = [channel for channel in range(3) if channel != index]
    return sum(
        (rgb := color(x, y))[index] >= 75 and
        rgb[index] >= rgb[other[0]] + 35 and
        rgb[index] >= rgb[other[1]] + 35
        for y in range(y0, y1, 2) for x in range(x0, x1, 2)
    )


def verify(home, red, blue, back, min_samples=12):
    navigation = compare_frames(home, red, blue, back)
    if not isinstance(min_samples, int) or isinstance(min_samples, bool) or min_samples < 1:
        raise ValueError("invalid minimum colored samples")
    a, b = frame_rgb(red), frame_rgb(blue)
    red_in_red = count_dominant(a, 0)
    blue_in_blue = count_dominant(b, 2)
    red_in_blue = count_dominant(b, 0)
    blue_in_red = count_dominant(a, 2)
    result = {"synthetic_red_pixels": red_in_red,
              "synthetic_blue_pixels": blue_in_blue,
              "red_pixels_in_blue_frame": red_in_blue,
              "blue_pixels_in_red_frame": blue_in_red,
              "original_visual_parity_verified": False,
              "synthetic_native_visual_acceptance": False}
    result.update(navigation)
    if red_in_red < min_samples or blue_in_blue < min_samples:
        raise ValueError(f"synthetic textured triangles not visible: {result}")
    if red_in_blue * 3 > red_in_red or blue_in_red * 3 > blue_in_blue:
        raise ValueError(f"texture color transition not model-specific: {result}")
    result["synthetic_native_visual_acceptance"] = True
    return result


def verify_legacy_mixed(path):
    frame = frame_rgb(path)
    upper = (0, 0, 256, 192)
    green = count_dominant(frame, 1, upper)
    red = count_dominant(frame, 0, upper)
    if min(green, red) < 12:
        raise ValueError(f"mixed legacy frame needs green texture and red face color: {green=}, {red=}")
    return {"legacy_green_texture_samples": green, "legacy_red_face_samples": red}


def png_chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def safe_png(xwd_path, png_path):
    width, height, rgb = frame_rgb(xwd_path)
    scan = b"".join(
        bytes([0]) + b"".join(bytes(rgb(x, y)) for x in range(width))
        for y in range(height)
    )
    out = (bytes((137, 80, 78, 71, 13, 10, 26, 10)) +
           png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
           png_chunk(b"IDAT", zlib.compress(scan, 9)) +
           png_chunk(b"IEND", b""))
    Path(png_path).write_bytes(out)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: c306_synthetic_texture_frame_gate.py HOME RED BLUE LEGACY BACK")
    home, red, blue, legacy, back = sys.argv[1:]
    # Preserve only the authored synthetic captures even when the strict
    # color gate fails; no native ROM or private original bytes are uploaded.
    for key, path in zip(("home", "red", "blue", "legacy", "back"), sys.argv[1:]):
        safe_png(path, f"c306-{key}.png")
    for key, path in (("red", red), ("blue", blue)):
        frame = frame_rgb(path)
        print("C306 diagnostic:", key,
              "top-screen red", count_dominant(frame, 0, (0, 0, 256, 192)),
              "blue", count_dominant(frame, 2, (0, 0, 256, 192)),
              flush=True)
    result = verify(home, red, blue, back)
    result.update(verify_legacy_mixed(legacy))
    print(json.dumps(result, sort_keys=True))
