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
    frames = [read_xwd(path) for path in (home, mapped, unmapped, back)]
    shape = frames[0][0]
    if any(item[0] != shape for item in frames):
        raise ValueError("synthetic ROM frame geometry changed")
    width, _, stride, pixel_size = shape

    def upper_delta(left, right):
        a, b = frames[left][1], frames[right][1]
        return sum(
            a[y * stride + x * pixel_size:y * stride + x * pixel_size + 3] !=
            b[y * stride + x * pixel_size:y * stride + x * pixel_size + 3]
            for y in range(64, 170, 2) for x in range(64, min(192, width), 2)
        )

    changed = upper_delta(1, 2)
    if changed < 20:
        raise ValueError("mapped vs unavailable species upper-screen region unchanged")
    # C252: a previous synthetic triangle must not persist behind HOME text.
    # Exclude the top-right debug heartbeat and both species-number glyphs.
    # This fails on the real pre-fix C251B capture (74 sampled pixels).
    stale = upper_delta(0, 3)
    if stale > 8:
        raise ValueError(f"stale 3D preview remains after B: {stale} pixels")
    result["mapped_vs_unmapped_upper_center_pixels"] = changed
    result["home_after_b_upper_center_pixels"] = stale
    result["original_geometry_rendering_verified"] = False
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: c251_synthetic_geometry_frame_gate.py HOME MAPPED UNMAPPED BACK")
    print("C251 synthetic geometry ROM diagnostic:", compare_synthetic(*sys.argv[1:]))
