#!/usr/bin/env python3
"""Audit user-supplied DS UI release assets; never fabricate missing screens.

Pass a directory containing authorized release files. This script only reads.
"""
import argparse
import json
from pathlib import Path

REQUIRED = (
    "ui/pages/t0_10_records.rgb555",
    "ui/pages/t1_00_home.rgb555",
    "ui/pages/t1_01_dex.rgb555",
    "ui/pages/t1_02_search.rgb555",
    "ui/pages/t1_03_moves.rgb555",
    "ui/pages/t1_04_types.rgb555",
    "ui/pages/t1_05_favorites.rgb555",
    "ui/pages/t1_06_challenge.rgb555",
    "ui/pages/t1_07_settings.rgb555",
    "ui/pages/t1_08_album.rgb555",
    "ui/pages/t1_09_ar.rgb555",
    "ui/pages/t1_10_records.rgb555",
    "ui/home_hotspots.p3hm",
    "ui/title/t0_title.rgb555",
    "ui/title/t1_title.rgb555",
    "ui/pages/t1_01_dex_overlay.rgb555",
)
FRAME_BYTES = 256 * 192 * 2


def inspect(root):
    root = Path(root).resolve()
    rows = []
    for relative in REQUIRED:
        target = root / relative
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            rows.append({"path": relative, "status": "unsafe"})
        elif not target.is_file():
            rows.append({"path": relative, "status": "missing"})
        elif relative.endswith(".rgb555") and target.stat().st_size != FRAME_BYTES:
            rows.append({"path": relative, "status": "invalid_size", "bytes": target.stat().st_size})
        elif relative.endswith(".p3hm"):
            rows.append({"path": relative, "status": "present_needs_format_and_geometry_verification"})
        else:
            rows.append({"path": relative, "status": "size_valid_needs_provenance_verification"})
    return {"schema": "ds-ui-release-presence-v1", "expected": len(REQUIRED),
            "missing": sum(r["status"] == "missing" for r in rows),
            "items": rows, "authenticity_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_root", type=Path)
    args = parser.parse_args()
    report = inspect(args.asset_root)
    print(json.dumps(report, indent=2))
    return 1 if any(r["status"] in ("unsafe", "invalid_size") for r in report["items"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
