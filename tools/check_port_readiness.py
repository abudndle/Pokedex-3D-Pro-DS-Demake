#!/usr/bin/env python3
"""Public, asset-free checks for required DS port source and build inputs."""
from pathlib import Path
import argparse
import json

REQUIRED = (
    "Makefile", "Makefile.native", "build_with_blocksds.sh",
    "source/verified_vertex_stream.c",
    "source/verified_primitive_stream.c",
    "source/verified_geometry_pair.c",
    "source/verified_primitive_bridge.c",
    "tools/validate_original_assets.py",
    "tools/c183_private_geometry_batch.py",
    "tools/c207_private_c5_xyz.py",
    "docs/PRIVATE_ASSET_BUILD.md",
    "docs/MODEL_RESTORATION_STATUS.md",
)
PRIVATE_GATES = (
    "verified original model/mesh provenance",
    "verified original material/texture mapping",
    "verified skeleton/animation bindings",
    "asset-integrated native ROM and emulator visual test",
    "complete original UI/gameplay and DSi AR acceptance",
)

def check(root):
    root = Path(root)
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    return {
        "public_source_complete": not missing,
        "missing_public_files": missing,
        "private_original_asset_gates": [
            {"requirement": name, "verified": False} for name in PRIVATE_GATES
        ],
        "full_original_port_verified": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = check(args.root)
    print(json.dumps(report, indent=2))
    return 0 if report["public_source_complete"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
