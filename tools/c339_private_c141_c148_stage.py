#!/usr/bin/env python3
"""Build a *private* C141 + C148 DS NitroFS development asset stage.

Never commit the output ZIP, Nintendo-derived assets, or original ROMs.
This is NOT a complete-game release/visual parity test.
"""
import argparse
import hashlib
import json
import pathlib
import zipfile

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def checked_names(z):
    names = z.namelist()
    if len(names) != len(set(names)):
        raise ValueError("duplicate archive names")
    for item in z.infolist():
        path = item.filename
        parts = path.split("/")
        if (not path or path.startswith("/") or "\\" in path or
            any(p in (".", "..") for p in parts) or
            item.file_size > 20 * 1024 * 1024 or
            ((item.external_attr >> 16) & 0o170000) == 0o120000):
            raise ValueError("unsafe archive member")
    if z.testzip() is not None:
        raise ValueError("archive CRC failure")
    return {name for name in names if not name.endswith("/")}

def build(base, skeletons, destination, report):
    if destination.exists():
        raise ValueError("private output already exists; refusing overwrite")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(skeletons) as b:
        aa, bb = checked_names(a), checked_names(b)
        if aa & bb:
            raise ValueError("duplicate paths across archives")
        if sum(n.startswith("preview/") and n.endswith(".ds3m") for n in aa) != 730:
            raise ValueError("C141 must contain 730 DS3M previews")
        if sum(n.startswith("skeleton/") and n.endswith(".p3sk") for n in bb) != 730:
            raise ValueError("C148 must contain 730 P3SK skeletons")
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=1, allowZip64=True) as output:
            for source, members in ((a, aa), (b, bb)):
                for name in sorted(members):
                    output.writestr(name, source.read(name))
    with zipfile.ZipFile(destination) as z:
        names = checked_names(z)
    missing = [
        "ui/pages/t1_00_home.rgb555", "ui/title/t0_title.rgb555",
        "ui/title/t1_title.rgb555", "ui/home_hotspots.p3hm",
        "ui/pages/t1_01_dex_overlay.rgb555"
    ]
    summary = {
        "stage_sha256": sha256(destination), "stage_bytes": destination.stat().st_size,
        "files": len(names), "preview_models": 730, "original_skeletons": 730,
        "texture_files": sum(n.startswith("textures/") for n in names),
        "missing_example_release_paths": [n for n in missing if n not in names],
        "release_ready": False,
        "privacy": "Keep original-derived assets private; never publish this ZIP or a ROM containing it."
    }
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c141", type=pathlib.Path, required=True)
    parser.add_argument("--c148", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(build(args.c141, args.c148, args.output, args.report), indent=2))
