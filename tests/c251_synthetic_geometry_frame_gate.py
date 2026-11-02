#!/usr/bin/env python3
"""C251: compare real DeSmuME frames from a synthetic-geometry NitroFS ROM.

A passing visual delta is NOT proof that original Pokémon geometry, materials,
textures or animations render correctly. The native C250 host test separately
proves P3SM -> P3VX/P3IX decoding; the screenshot check is diagnostic only.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c235_emulator_frame_gate import compare_frames, read_xwd


def compare_synthetic(home, mapped, unmapped, back):
    result = compare_frames(home, mapped, unmapped, back)
    shape_a, frame_a = read_xwd(mapped)
    shape_b, frame_b = read_xwd(unmapped)
    if shape_a != shape_b:
        raise ValueError("synthetic ROM frame geometry changed")
    width, _, stride, pixel_size = shape_a
    changed = sum(
        frame_a[y * stride + x * pixel_size:y * stride + x * pixel_size + 3] !=
        frame_b[y * stride + x * pixel_size:y * stride + x * pixel_size + 3]
        for y in range(64, 170, 2) for x in range(64, min(192, width), 2)
    )
    if changed < 20:
        raise ValueError("mapped vs unavailable species upper-screen region unchanged")
    result["mapped_vs_unmapped_upper_center_pixels"] = changed
    result["original_geometry_rendering_verified"] = False
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: c251_synthetic_geometry_frame_gate.py HOME MAPPED UNMAPPED BACK")
    print("C251 synthetic geometry ROM diagnostic:", compare_synthetic(*sys.argv[1:]))
