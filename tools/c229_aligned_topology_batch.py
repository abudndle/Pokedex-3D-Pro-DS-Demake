#!/usr/bin/env python3
"""C229: extend C227 private C5 topology candidate coverage with 4-byte mesh alignment.

These are *heuristic* candidate indices. No original 3DS provenance, source
geometry equivalence, UVs, materials or Nintendo DS rendering are certified.
Original source and per-model outputs must stay outside the public checkout.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import zipfile

from c5_dual_table_parser import parse
from c227_private_topology_batch import (
    _archive_roster, _outside_repo, _private_json, find_topology, inspect_faces,
    MAX_MEMBER_BYTES,
)

TRIANGLE_PREFIX = struct.pack("<3H", 0, 1, 2)
SCHEMA = "p3d-c229-private-c5-topology-candidates-v1"


def _descriptors(data):
    meta = parse(data)
    if not meta["structural_checks_passed"]:
        raise ValueError("C5 descriptor structural validation failed")
    first, second = meta["first_table"], meta["second_table"]
    if not first or len(first) != len(second):
        raise ValueError("unpaired C5 descriptor tables")
    vertices = [entry["record_count"] for entry in first]
    indices = [entry["low16"] for entry in second]
    if any(count < 3 for count in vertices):
        raise ValueError("invalid vertex record count")
    if any(entry["high16"] != 2 or count < 3 or count % 3
           for entry, count in zip(second, indices)):
        raise ValueError("unsupported original index record layout")
    scan_start = int(second[-1]["candidate_end_offset"], 16)
    return meta, vertices, indices, scan_start


def find_aligned_candidate(data, model=None):
    """Find one full strict candidate, using a TRI prefix and aligned mesh starts.

    The index stream begins on a 4-byte boundary; each later mesh begins at
    align_up(previous_mesh_end, 4). Requiring one full uniquely matching stream
    avoids silently choosing one of several plausible byte regions.
    """
    meta, vertices, indices, scan_start = _descriptors(data)
    candidates = []
    offset = data.find(TRIANGLE_PREFIX, scan_start)
    while offset >= 0:
        if offset % 4 == 0:
            position = offset
            groups = []
            for mesh, (vertex_count, index_count) in enumerate(zip(vertices, indices)):
                byte_count = index_count * 2
                if position > len(data) or byte_count > len(data) - position:
                    break
                values = struct.unpack_from("<" + str(index_count) + "H", data, position)
                try:
                    faces = inspect_faces(values, vertex_count)
                except ValueError:
                    break
                groups.append({
                    "mesh": mesh, "vertex_count": vertex_count,
                    "triangle_count": len(faces),
                    "triangles": [list(face) for face in faces],
                })
                position += byte_count
                if mesh + 1 != len(vertices):
                    position = (position + 3) & ~3
            else:
                candidates.append((offset, position, groups))
                if len(candidates) > 1:
                    break
        offset = data.find(TRIANGLE_PREFIX, offset + 2)

    if len(candidates) != 1:
        raise ValueError(f"expected one aligned C5 topology candidate, found {len(candidates)}")
    start, end, groups = candidates[0]
    return {
        "schema": SCHEMA,
        "source": "original-c5",
        "model": model,
        "candidate_method": "c229-triangle-prefix-four-byte-aligned",
        "sha256_decoded_c5": meta["sha256"],
        "decoded_c5_size": len(data),
        "topology_start": start,
        "topology_end": end,
        "mesh_count": len(groups),
        "vertex_count": sum(vertices),
        "triangle_count": sum(indices) // 3,
        "meshes": groups,
        "independent_topology_provenance_verified": False,
        "complete_models_verified": False,
        "native_ds_rendering_verified": False,
        "scope": "Heuristic candidate face order only. Independent original-reference verification required.",
    }


def recover_candidate(data, model=None):
    """Never replace a C227 candidate with a different C229 hypothesis."""
    try:
        previous = find_topology(data, model)
    except ValueError:
        return find_aligned_candidate(data, model)
    previous["schema"] = SCHEMA
    previous["candidate_method"] = "c227-quad-prefix-contiguous"
    previous["independent_topology_provenance_verified"] = False
    previous["scope"] = "C227 heuristic topology only; original face order and DS rendering unverified."
    return previous


def audit_archives(archive_dir, output_dir):
    archive_dir = _outside_repo(archive_dir, "private C56 source")
    output_dir = _outside_repo(output_dir, "private candidate output")
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("private candidate output must not already exist")
    members = _archive_roster(archive_dir)  # Checks all 730 names and byte budgets FIRST.
    output_dir.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix=".c229-private-", dir=output_dir.parent))
    os.chmod(staging, 0o700)
    try:
        topology = staging / "topology"
        topology.mkdir(mode=0o700)
        totals = Counter()
        failures = Counter()
        for archive_path, name, expected_size, model in members:
            with zipfile.ZipFile(archive_path) as archive:
                with archive.open(name) as stream:
                    data = stream.read(MAX_MEMBER_BYTES + 1)
            if len(data) != expected_size or len(data) > MAX_MEMBER_BYTES:
                raise ValueError("source ZIP member size mismatch")
            try:
                record = recover_candidate(data, model)
            except ValueError as exc:
                failures[str(exc).split(":")[0][:96]] += 1
                continue
            _private_json(topology / (model + ".json"), record)
            totals[record["candidate_method"]] += 1
            totals["mesh_groups"] += record["mesh_count"]
            totals["vertices"] += record["vertex_count"]
            totals["triangles"] += record["triangle_count"]
        accepted = (totals["c227-quad-prefix-contiguous"] +
                    totals["c229-triangle-prefix-four-byte-aligned"])
        result = {
            "schema": "p3d-c229-private-c5-topology-audit-v1",
            "source_model_records_checked": len(members),
            "c227_preserved_candidates": totals["c227-quad-prefix-contiguous"],
            "c229_additional_aligned_candidates": totals["c229-triangle-prefix-four-byte-aligned"],
            "combined_candidate_models": accepted,
            "unresolved_records": len(members) - accepted,
            "candidate_mesh_groups": totals["mesh_groups"],
            "candidate_vertices": totals["vertices"],
            "candidate_triangles": totals["triangles"],
            "failure_categories": dict(sorted(failures.items())),
            "independent_topology_provenance_verified": False,
            "complete_models_verified": False,
            "native_ds_rendering_verified": False,
        }
        _private_json(staging / "summary.json", result)
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError("private candidate output appeared during audit")
        os.rename(staging, output_dir)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = audit_archives(args.archive_dir, args.output_dir)
    # No per-model source bytes, candidate triangle arrays or source digests on stdout.
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
