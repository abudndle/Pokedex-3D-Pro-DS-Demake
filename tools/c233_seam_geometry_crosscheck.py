#!/usr/bin/env python3
"""C233: private, seam-aware *geometric* triangle comparison.

Unlike strict C228, this accepts duplicate XYZ vertices created by UV seams,
including different source/reference vertex counts. It proves only coordinate-
space triangle equivalence, NEVER original index topology, UVs, or provenance.
"""
import argparse
from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path

from c180_private_c5_coverage import write_private_report
from c228_reference_topology_crosscheck import (
    _bucket, _faces, _orientation, _private_input, _vertices, parse_obj,
    DS_TRIANGLE_LIMIT, DS_VERTEX_LIMIT,
)


def _reference_classes(vertices, tolerance):
    """Group exactly coincident positions; reject near-but-distinct references."""
    exact = {}
    buckets = defaultdict(list)
    ids = []
    for point in vertices:
        if point in exact:
            ids.append(exact[point])
            continue
        key = _bucket(point, tolerance)
        for delta in itertools.product((-1, 0, 1), repeat=3):
            near = tuple(key[i] + delta[i] for i in range(3))
            for other_id, other in buckets.get(near, ()):
                if all(abs(point[i] - other[i]) <= tolerance for i in range(3)):
                    raise ValueError("ambiguous distinct reference XYZ within tolerance")
        identifier = len(exact)
        exact[point] = identifier
        buckets[key].append((identifier, point))
        ids.append(identifier)
    return ids, buckets, len(exact)


def _map_source(source, buckets, tolerance):
    ids = []
    for point in source:
        key = _bucket(point, tolerance)
        candidates = set()
        for delta in itertools.product((-1, 0, 1), repeat=3):
            near = tuple(key[i] + delta[i] for i in range(3))
            for identifier, reference in buckets.get(near, ()):
                if all(abs(point[i] - reference[i]) <= tolerance for i in range(3)):
                    candidates.add(identifier)
        if len(candidates) != 1:
            raise ValueError("ambiguous or unmatched source XYZ class")
        ids.append(next(iter(candidates)))
    return ids


def _geometric_faces(faces, ids):
    result = []
    for face in faces:
        mapped = tuple(ids[index] for index in face)
        if len(set(mapped)) != 3:
            raise ValueError("geometrically degenerate triangle after seam collapse")
        result.append(mapped)
    return result


def verify_geometric_mesh(source_xyz, source_faces, reference_xyz,
                          reference_faces, tolerance=1e-5):
    """Compare triangle geometry, preserving multiplicity and global winding."""
    import math
    if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
            or not math.isfinite(tolerance) or not 0 < tolerance <= 0.001):
        raise ValueError("invalid coordinate tolerance")
    source = _vertices(source_xyz)
    reference = _vertices(reference_xyz)
    left = _faces(source_faces, len(source))
    right = _faces(reference_faces, len(reference))
    reference_ids, buckets, unique_count = _reference_classes(reference, tolerance)
    source_ids = _map_source(source, buckets, tolerance)
    if set(source_ids) != set(reference_ids):
        raise ValueError("source/reference coordinate class coverage mismatch")
    mapped_left = _geometric_faces(left, source_ids)
    mapped_right = _geometric_faces(right, reference_ids)
    left_unordered = Counter(tuple(sorted(f)) for f in mapped_left)
    right_unordered = Counter(tuple(sorted(f)) for f in mapped_right)
    if left_unordered != right_unordered:
        raise ValueError("source/reference geometric triangle coverage mismatch")
    reference_winding = Counter(_orientation(f) for f in mapped_right)
    if Counter(_orientation(f) for f in mapped_left) == reference_winding:
        winding = "same"
    elif Counter(_orientation(tuple(reversed(f))) for f in mapped_left) == reference_winding:
        winding = "globally_reversed"
    else:
        raise ValueError("mixed or inconsistent geometric winding")
    return {
        "schema": "p3d-c233-private-seam-geometric-crosscheck-v1",
        "geometric_face_equivalence_verified": True,
        "exact_index_topology_verified": False,
        "uv_seam_vertex_identity_verified": False,
        "independent_original_3ds_provenance_verified": False,
        "native_ds_rendering_verified": False,
        "source_vertex_count": len(source),
        "reference_vertex_count": len(reference),
        "unique_position_classes": unique_count,
        "source_seam_duplicate_vertices": len(source) - len(set(source_ids)),
        "reference_seam_duplicate_vertices": len(reference) - unique_count,
        "triangle_count": len(left),
        "coincident_triangle_multiplicity": any(n > 1 for n in left_unordered.values()),
        "winding": winding,
        "within_ds_vertex_budget": len(source) <= DS_VERTEX_LIMIT,
        "within_ds_triangle_budget": len(left) <= DS_TRIANGLE_LIMIT,
    }


def run_private(source_json, reference_obj, report, tolerance=1e-5):
    source = json.loads(_private_input(source_json).read_text(encoding="utf-8"))
    reference = _private_input(reference_obj).read_text(encoding="utf-8")
    if not isinstance(source, dict) or set(source) != {"vertices", "triangles"}:
        raise ValueError("source must contain exactly vertices and triangles")
    xyz, faces = parse_obj(reference)
    result = verify_geometric_mesh(source["vertices"], source["triangles"],
                                   xyz, faces, tolerance=tolerance)
    write_private_report(Path(report), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--reference-obj", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=1e-5)
    args = parser.parse_args()
    result = run_private(args.source_json, args.reference_obj, args.report, args.tolerance)
    print("C233 geometric triangles:", result["triangle_count"],
          "seam duplicates:", result["source_seam_duplicate_vertices"],
          "original topology verified: False")


if __name__ == "__main__":
    main()
