#!/usr/bin/env python3
"""C227: recover strict original C5 triangle topology into a private workspace.

Only model index connectivity is exported. This does not decode positions, UVs,
materials, textures, skin weights, or animations. Per-model face lists are
derived from private Nintendo source data and MUST remain outside this repo.
"""
import argparse
import os
import shutil
import stat
import tempfile
from collections import Counter
import json
import re
import struct
import zipfile
from pathlib import Path

from c5_dual_table_parser import parse

START_TRIANGLES = struct.pack("<6H", 0, 1, 2, 0, 2, 3)
MODEL_MEMBER = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")
EXPECTED_MODELS = {f"p{i:03d}" for i in range(734) if i not in (721, 722, 723, 724)}
REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_ZIP_ENTRIES = 2048


def inspect_faces(values, vertex_count):
    if not values or len(values) % 3:
        raise ValueError("index count not divisible by three")
    faces = [tuple(values[i:i + 3]) for i in range(0, len(values), 3)]
    if min(values) < 0 or max(values) >= vertex_count:
        raise ValueError("index outside source vertex count")
    if any(len(set(face)) != 3 for face in faces):
        raise ValueError("degenerate triangle")
    if len(set(faces)) != len(faces):
        raise ValueError("duplicate triangle")
    referenced = set(values)
    if len(referenced) != vertex_count:
        raise ValueError("not every source vertex is referenced")
    edges = Counter(tuple(sorted(edge)) for a, b, c in faces
                    for edge in ((a, b), (b, c), (c, a)))
    if any(count > 2 for count in edges.values()):
        raise ValueError("non-manifold edge")
    return faces


def find_topology(data, model=None):
    """Find exactly one full index region that validates against all C5 meshes."""
    meta = parse(data)
    if not meta["structural_checks_passed"]:
        raise ValueError("C5 descriptor bounds validation failed")
    first, second = meta["first_table"], meta["second_table"]
    if not first or len(first) != len(second):
        raise ValueError("unpaired geometry descriptor tables")
    vertex_counts = [row["record_count"] for row in first]
    byte_counts = [2 * row["low16"] for row in second]
    if any(row["high16"] != 2 or row["low16"] < 3 or row["low16"] % 3
           for row in second):
        raise ValueError("unsupported per-mesh index width or count")
    if any(count < 3 for count in vertex_counts):
        raise ValueError("invalid source vertex count")

    scan_start = int(second[-1]["candidate_end_offset"], 16)
    candidates = []
    offset = data.find(START_TRIANGLES, scan_start)
    while offset >= 0:
        position = offset
        groups = []
        try:
            for vertex_count, byte_count in zip(vertex_counts, byte_counts):
                if position > len(data) or byte_count > len(data) - position:
                    raise ValueError("truncated topology region")
                values = struct.unpack_from("<" + str(byte_count // 2) + "H",
                                            data, position)
                groups.append(inspect_faces(values, vertex_count))
                position += byte_count
            candidates.append((offset, groups, position))
        except ValueError:
            pass
        offset = data.find(START_TRIANGLES, offset + 2)

    if len(candidates) != 1:
        raise ValueError(f"expected unique fully validated index region; got {len(candidates)}")
    offset, groups, end = candidates[0]
    return {
        "schema": "p3d-c227-private-original-c5-topology-v1",
        "source": "original-c5",
        "model": model,
        "sha256_decoded_c5": meta["sha256"],
        "decoded_c5_size": len(data),
        "topology_start": offset,
        "topology_end": end,
        "mesh_count": len(groups),
        "vertex_count": sum(vertex_counts),
        "triangle_count": sum(len(group) for group in groups),
        "meshes": [
            {"mesh": index, "vertex_count": vertex_counts[index],
             "triangle_count": len(groups[index]),
             "triangles": [list(face) for face in groups[index]]}
            for index in range(len(groups))
        ],
        "scope": "Topology only; positions, materials, UVs and rendering are not verified.",
        "complete_models_verified": False,
        "native_ds_rendering_verified": False,
    }


def _outside_repo(path, label):
    resolved = Path(path).expanduser().resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError(f"{label} must be outside the public repository")
    return resolved


def _private_json(path, payload):
    """Write a 0600 file atomically; never follow an existing destination link."""
    if path.is_symlink():
        raise ValueError("private output symlink refused")
    fd, temporary = tempfile.mkstemp(prefix=".c227-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _archive_roster(archive_dir):
    """Validate all ZIP metadata before decompressing or writing any model."""
    members = []
    seen = set()
    total_bytes = 0
    for part in (1, 2, 3):
        path = archive_dir / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_ENTRIES:
                raise ValueError("ZIP entry count budget exceeded")
            if len({info.filename for info in infos}) != len(infos):
                raise ValueError("duplicate ZIP member name")
            for info in infos:
                match = MODEL_MEMBER.fullmatch(info.filename)
                if match is None:
                    raise ValueError("unexpected private C5 archive member")
                model = f"p{int(match.group(1)):03d}"
                if model in seen:
                    raise ValueError("duplicate source model")
                seen.add(model)
                mode = info.external_attr >> 16
                if (info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits & 1
                        or info.file_size > MAX_MEMBER_BYTES):
                    raise ValueError("unsafe or oversized C5 archive member")
                if info.file_size < 0 or total_bytes + info.file_size > MAX_TOTAL_BYTES:
                    raise ValueError("aggregate C5 byte budget exceeded")
                total_bytes += info.file_size
                members.append((path, info.filename, info.file_size, model))
    if seen != EXPECTED_MODELS:
        raise ValueError("private C5 roster is incomplete or unexpected")
    return members


def audit_archives(archive_dir, output_dir):
    archive_dir = _outside_repo(archive_dir, "private archive directory")
    output_dir = _outside_repo(output_dir, "private output directory")
    # Never reuse an old report: partial results must not look like a full audit.
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("private output directory must not already exist")
    members = _archive_roster(archive_dir)
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix=".c227-private-", dir=parent))
    os.chmod(staging, 0o700)
    try:
        topology_dir = staging / "topology"
        topology_dir.mkdir(mode=0o700)
        totals = Counter()
        failures = Counter()
        for archive_path, name, expected_size, model in members:
            with zipfile.ZipFile(archive_path) as archive:
                with archive.open(name) as stream:
                    data = stream.read(MAX_MEMBER_BYTES + 1)
            if len(data) != expected_size or len(data) > MAX_MEMBER_BYTES:
                raise ValueError("C5 decompressed member size mismatch")
            try:
                result = find_topology(data, model)
            except ValueError as exc:
                failures[str(exc).split(":")[0][:100]] += 1
                continue
            _private_json(topology_dir / f"{model}.json", result)
            totals["models_with_topology"] += 1
            totals["meshes"] += result["mesh_count"]
            totals["vertices"] += result["vertex_count"]
            totals["triangles"] += result["triangle_count"]
        summary = {
            "schema": "p3d-c227-private-c5-topology-summary-v1",
            "c5_models_audited": len(members),
            "models_with_strict_topology": totals["models_with_topology"],
            "models_without_strict_topology": len(members) - totals["models_with_topology"],
            "verified_mesh_groups": totals["meshes"],
            "verified_vertices_referenced": totals["vertices"],
            "verified_triangles": totals["triangles"],
            "failure_categories": dict(sorted(failures.items())),
            "per_model_topology_files": "topology/pNNN.json (private; do not publish)",
            "independent_topology_provenance_verified": False,
            "complete_models_verified": False,
            "native_ds_rendering_verified": False,
        }
        _private_json(staging / "summary.json", summary)
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError("private output destination appeared during audit")
        os.rename(staging, output_dir)
        return summary
    finally:
        if staging.exists():
            shutil.rmtree(staging)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit_archives(args.archive_dir, args.output_dir),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
