#!/usr/bin/env python3
"""Validate a private, locally supplied original-asset build manifest.

No original game data is stored or distributed by this script.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

def validate(manifest_path: Path, asset_root: Path):
    errors = []
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Cannot read asset manifest: {exc}"]
    if data.get("format") != "p3d-ds-original-assets-v1":
        errors.append("Unsupported manifest format")
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        return errors + ["Manifest must list at least one required original asset"]
    root = asset_root.resolve()
    seen = set()
    for item in assets:
        if not isinstance(item, dict):
            errors.append("Invalid asset entry")
            continue
        name = item.get("path")
        if not isinstance(name, str) or not name or name in seen:
            errors.append(f"Invalid or duplicate asset path: {name!r}")
            continue
        seen.add(name)
        rel = Path(name)
        path = (root / rel).resolve()
        if rel.is_absolute() or path == root or root not in path.parents:
            errors.append(f"Unsafe asset path: {name}")
            continue
        if not path.is_file():
            errors.append(f"Missing required original asset: {name}")
            continue
        size = item.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            errors.append(f"Missing/invalid expected size for {name}")
        elif path.stat().st_size != size:
            errors.append(f"Size mismatch for {name}")
        digest = item.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"Missing/invalid SHA-256 for {name}")
        else:
            try:
                int(digest, 16)
            except ValueError:
                errors.append(f"Invalid SHA-256 hex for {name}")
                continue
            h = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            if h.hexdigest().lower() != digest.lower():
                errors.append(f"SHA-256 mismatch for {name}")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    errors = validate(args.manifest, args.root)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Original-asset manifest verified; no copyrighted data copied.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
