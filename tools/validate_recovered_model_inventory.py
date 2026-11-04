#!/usr/bin/env python3
"""Check private recovered C56/C62/C63 archive coverage without shipping game assets."""
import argparse, io, json, re, zipfile
from pathlib import Path

def scan(root):
    kinds = {
        "c5": [f"Pokedex3D_C56_Decoded_C5_Part_{i}_of_3.zip" for i in (1, 2, 3)],
        "c62": ["Pokedex3D_C62_528_UV_Model_Exports.zip"],
        "c63": ["Pokedex3D_C63_Partial_UV_Recovery_162_Models.zip"],
    }
    result = {"counts": {}, "errors": []}
    identifiers = {}
    for kind, archives in kinds.items():
        ids = []
        for filename in archives:
            with zipfile.ZipFile(root / filename) as archive:
                suffix = "c5" if kind == "c5" else "obj"
                members = [s for s in archive.namelist() if re.search(r"/p\d{3}\." + suffix + r"$", s)]
                for member in members:
                    index = int(re.search(r"/p(\d{3})\.", member).group(1))
                    ids.append(index)
                    if kind == "c5":
                        continue
                    vertices = uvs = faces = mapped = 0
                    with archive.open(member) as data:
                        for line in io.TextIOWrapper(data, encoding="utf-8", errors="replace"):
                            if line.startswith("v "):
                                vertices += 1
                            elif line.startswith("vt "):
                                uvs += 1
                            elif line.startswith("f "):
                                faces += 1
                                has_uv = False
                                for token in line.split()[1:]:
                                    parts = token.split("/")
                                    try:
                                        vertex = int(parts[0])
                                        assert vertex and abs(vertex) <= vertices
                                        if len(parts) > 1 and parts[1]:
                                            uv = int(parts[1])
                                            assert uv and abs(uv) <= uvs
                                            has_uv = True
                                    except (AssertionError, ValueError):
                                        result["errors"].append(f"{kind} p{index:03d}: invalid face reference")
                                mapped += has_uv
                    if not all((vertices, uvs, faces, mapped)):
                        result["errors"].append(f"{kind} p{index:03d}: missing geometry/UV references")
        if len(ids) != len(set(ids)):
            result["errors"].append(f"{kind}: duplicate model identifier")
        identifiers[kind] = set(ids)
        result["counts"][kind] = len(ids)
    result["overlap"] = sorted(identifiers["c62"] & identifiers["c63"])
    result["uncovered_c5"] = sorted(identifiers["c5"] - identifiers["c62"] - identifiers["c63"])
    if result["overlap"]:
        result["errors"].append("C62/C63 model identifiers overlap")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_directory", type=Path, help="directory of private recovered ZIP files")
    args = parser.parse_args()
    try:
        report = scan(args.archive_directory)
        print(json.dumps(report, indent=2))
        raise SystemExit(1 if report["errors"] else 0)
    except (OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"Archive validation failed: {exc}\n")
