#!/usr/bin/env python3
"""Private, fail-closed 730-model P3VX/P3IX native draw-path batch audit.

All proprietary sidecars and SHA-bearing reports must remain outside GitHub.
This verifies the existing DS loader/draw adapter, not original C5 provenance.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import sys
import struct
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c180_private_c5_coverage import EXPECTED, write_private_report

REPO = Path(__file__).resolve().parents[1]
MODEL_NAME = re.compile(r"p([0-9]{3})\.(p3vx|p3ix)\Z")
MAX_INDEX_BYTES = 10 + 64 * 6 + 1800 * 6
MAX_VERTEX_BYTES = 16 + 64 * 8 + 8192 * 6
NATIVE_SOURCES = (
    "source/verified_vertex_stream.c", "source/verified_primitive_stream.c",
    "source/verified_primitive_bridge.c", "source/verified_geometry_pair.c",
    "source/verified_primitive_draw.c", "tests/c179_private_geometry_draw_probe.c",
)


def outside_repo(path):
    resolved = Path(path).expanduser().resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("private geometry and reports must stay outside public repository")
    return resolved


def index_triangle_count(path, model):
    """Read only bounded metadata; the C179 probe verifies all vertex references."""
    if path.stat().st_size > MAX_INDEX_BYTES:
        raise ValueError("oversized index stream")
    data = path.read_bytes()
    if len(data) < 10 or data[:4] != b"P3IX":
        raise ValueError("invalid index header")
    version, found, meshes = struct.unpack_from("<HHH", data, 4)
    if version != 1 or found != model or not 1 <= meshes <= 64:
        raise ValueError("index identity or mesh count mismatch")
    pos, triangles, previous = 10, 0, -1
    for _ in range(meshes):
        if pos + 6 > len(data):
            raise ValueError("truncated index mesh")
        mesh, count = struct.unpack_from("<HI", data, pos)
        pos += 6
        if mesh <= previous or mesh >= 64 or not count or count > 1800 - triangles:
            raise ValueError("invalid index mesh or triangle count")
        previous = mesh
        size = count * 6
        if size > len(data) - pos:
            raise ValueError("truncated index triangles")
        pos += size
        triangles += count
    if pos != len(data):
        raise ValueError("trailing index bytes")
    return triangles


def audit(root, probe, roster=None):
    candidate = Path(root).expanduser().absolute()
    if any(p.is_symlink() for p in (candidate, *candidate.parents)):
        raise ValueError("private geometry directory symlink rejected")
    root = outside_repo(root)
    if not root.is_dir():
        raise ValueError("private geometry directory missing")
    requested = list(EXPECTED if roster is None else roster)
    if not requested:
        raise ValueError('empty roster')
    if any(type(model) is not int or model not in EXPECTED for model in requested):
        raise ValueError("invalid model roster")
    roster = set(requested)
    if len(roster) != len(requested):
        raise ValueError("duplicate model roster entries")
    probe_path = Path(probe).expanduser().absolute()
    if any(part.is_symlink() for part in (probe_path, *probe_path.parents)):
        raise ValueError('native draw probe symlink rejected')
    probe = probe_path.resolve()
    if not probe.is_file():
        raise ValueError("native draw probe missing")
    if not os.access(probe, os.X_OK):
        raise ValueError("native draw probe not executable")
    if not os.access(probe, os.R_OK):
        raise ValueError("native draw probe not readable")
    unexpected = []
    for path in root.iterdir():
        match = MODEL_NAME.fullmatch(path.name)
        if match is None or int(match.group(1)) not in roster or path.is_symlink() or not path.is_file():
            unexpected.append(path.name)
    if unexpected:
        raise ValueError("unexpected private geometry entries: " + str(len(unexpected)))
    records = {}
    for model in sorted(roster):
        name = f"p{model:03d}"
        vx, ix = root / (name + ".p3vx"), root / (name + ".p3ix")
        if not vx.exists() or not ix.exists():
            records[name] = {"error": "missing_pair"}
            continue
        if vx.is_symlink() or ix.is_symlink() or not vx.is_file() or not ix.is_file():
            records[name] = {"error": "unsafe_pair"}
            continue
        try:
            if vx.stat().st_size > MAX_VERTEX_BYTES:
                raise ValueError("oversized vertex stream")
            triangles = index_triangle_count(ix, model)
            run = subprocess.run(
                [str(probe), str(vx), str(ix), str(model), str(triangles)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
                check=False,
            )
            if run.returncode:
                raise ValueError("native probe rejected pair")
            records[name] = {
                "triangles": triangles,
                "p3vx_sha256": hashlib.sha256(vx.read_bytes()).hexdigest(),
                "p3ix_sha256": hashlib.sha256(ix.read_bytes()).hexdigest(),
                "native_gl_path_verified": True,
                "original_c5_provenance_verified": False,
            }
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            records[name] = {"error": type(exc).__name__}
    passed = sum("error" not in record for record in records.values())
    return {
        "expected": len(roster), "native_pairs_verified": passed,
        "all_pairs_verified": passed == len(roster),
        "original_c5_provenance_verified": False,
        "private_asset_emulator_verified": False,
        "models": records,
    }


def build_probe(output):
    cmd = [os.environ.get("CC", "cc"), "-std=c11", "-O2", "-Wall",
           "-Wextra", "-Werror", "-DC7_TEST_HOST", "-Isource"]
    cmd.extend(NATIVE_SOURCES)
    cmd.extend(["-o", str(output)])
    subprocess.run(cmd, cwd=REPO, check=True, capture_output=True, timeout=120)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    outside_repo(args.root)
    outside_repo(args.report)
    with tempfile.TemporaryDirectory() as directory:
        probe = Path(directory) / "native-pair-probe"
        build_probe(probe)
        result = audit(args.root, probe)
    write_private_report(args.report, result)
    print("C183 native draw pairs", result["native_pairs_verified"], "/", result["expected"],
          "(original C5 provenance and emulator rendering NOT verified)")
    return 0 if result["all_pairs_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
