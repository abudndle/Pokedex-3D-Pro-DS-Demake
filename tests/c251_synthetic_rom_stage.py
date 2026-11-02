#!/usr/bin/env python3
"""C251: stage ONLY synthetic P3VX/P3IX and diagnostic P3SM for ROM CI.

This never reads or publishes original Nintendo files. A successful test is
evidence of native integration mechanics, not source topology or visual parity.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from c249_private_geometry_nitrofs import stage
from test_c249_private_geometry_nitrofs import fixture


def prepare(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError("C251 requires an existing empty, non-symlinked temp directory")
    source, mapping, destination = fixture(root)
    report = stage(source, mapping, destination)
    if (report["species_slots"], report["unique_models"]) != (2, 2):
        raise ValueError("unexpected synthetic fixture count")
    if (report["original_species_resource_mapping_verified"] or
            report["asset_integrated_emulator_verified"] or
            report["original_game_release_ready"]):
        raise ValueError("diagnostic fixture must never assert original-asset proof")
    values = struct.unpack("<4sHH649H", (destination / "models/species_map.p3sm").read_bytes())
    if (values[:3] != (b"P3SM", 1, 649) or
            values[3] != 2 or values[4] != 0xffff or values[-1] != 3 or
            any(v != 0xffff for v in values[5:-1])):
        raise ValueError("diagnostic species mapping not isolated")
    expected = {"p002.p3vx", "p002.p3ix", "p003.p3vx", "p003.p3ix"}
    if {p.name for p in (destination / "geometry").iterdir()} != expected:
        raise ValueError("synthetic geometry files not exactly as expected")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("empty_temp_dir", type=Path)
    args = parser.parse_args()
    destination = prepare(args.empty_temp_dir)
    print(json.dumps({"schema": "c251-synthetic-native-geometry-ci-v1",
                      "nitrofs": str(destination),
                      "diagnostic_species_slots": 2,
                      "native_synthetic_pairs": 2,
                      "original_assets_included": False,
                      "original_rendering_verified": False}, sort_keys=True))


if __name__ == "__main__":
    main()
