#!/usr/bin/env python3
"""C228: independently compare private C5 topology candidates with reference OBJ.

This is an asset-free source tool. Source geometry and reports stay private.
Face equivalence to an OBJ reference does NOT by itself prove 3DS provenance.
"""
import argparse
from collections import Counter, defaultdict
import itertools
import json
import math
from pathlib import Path

from c180_private_c5_coverage import write_private_report

ROOT = Path(__file__).resolve().parents[1]
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_VERTICES = 200000
MAX_TRIANGLES = 500000
DS_VERTEX_LIMIT = 8192
DS_TRIANGLE_LIMIT = 1800


def _vertices(rows):
    if not isinstance(rows, list) or not 3 <= len(rows) <= MAX_VERTICES:
        raise ValueError("invalid vertex count")
    vertices = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            raise ValueError("invalid XYZ record")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in row):
            raise ValueError("non-numeric XYZ")
        point = tuple(float(v) for v in row)
        if not all(math.isfinite(v) for v in point):
            raise ValueError("non-finite XYZ")
        vertices.append(point)
    return vertices


def _faces(rows, vertex_count):
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_TRIANGLES:
        raise ValueError("invalid triangle count")
    faces = []
    for face in rows:
        if not isinstance(face, (list, tuple)) or len(face) != 3:
            raise ValueError("non-triangle face")
        if any(type(index) is not int or index < 0 or index >= vertex_count
               for index in face):
            raise ValueError("out-of-range face index")
        if len(set(face)) != 3:
            raise ValueError("degenerate face")
        faces.append(tuple(face))
    canonical = [tuple(sorted(face)) for face in faces]
    if len(set(canonical)) != len(canonical):
        raise ValueError("duplicate face")
    return faces


def _orientation(face):
    a, b, c = face
    return min((a, b, c), (b, c, a), (c, a, b))


def _bucket(point, tolerance):
    return tuple(math.floor(value / tolerance) for value in point)


def _vertex_mapping(source, reference, tolerance):
    if len(source) != len(reference):
        raise ValueError("source/reference vertex counts differ")
    buckets = defaultdict(list)
    for index, point in enumerate(reference):
        buckets[_bucket(point, tolerance)].append(index)
    used = set()
    mapping = []
    for point in source:
        key = _bucket(point, tolerance)
        matches = []
        for delta in itertools.product((-1, 0, 1), repeat=3):
            neighbor = tuple(key[i] + delta[i] for i in range(3))
            for index in buckets.get(neighbor, ()):
                if all(abs(point[i] - reference[index][i]) <= tolerance
                       for i in range(3)):
                    matches.append(index)
        if len(matches) != 1 or matches[0] in used:
            raise ValueError("ambiguous or unmatched source XYZ")
        mapping.append(matches[0])
        used.add(matches[0])
    return mapping


def verify_mesh(source_xyz, source_faces, reference_xyz, reference_faces,
                tolerance=1e-5):
    """Require exact face coverage after a unique, bounded XYZ correspondence."""
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 < tolerance <= 0.001:
        raise ValueError("invalid coordinate tolerance")
    source = _vertices(source_xyz)
    reference = _vertices(reference_xyz)
    left = _faces(source_faces, len(source))
    right = _faces(reference_faces, len(reference))
    mapping = _vertex_mapping(source, reference, tolerance)
    remapped = [tuple(mapping[i] for i in face) for face in left]
    if Counter(tuple(sorted(f)) for f in remapped) != Counter(tuple(sorted(f)) for f in right):
        raise ValueError("source/reference triangle coverage mismatch")
    reference_winding = Counter(_orientation(f) for f in right)
    if Counter(_orientation(f) for f in remapped) == reference_winding:
        winding = "same"
    elif Counter(_orientation(tuple(reversed(f))) for f in remapped) == reference_winding:
        winding = "globally_reversed"
    else:
        raise ValueError("mixed or inconsistent triangle winding")
    return {
        "schema": "p3d-c228-private-reference-face-crosscheck-v1",
        "reference_face_equivalence_verified": True,
        "unique_vertex_correspondence_verified": True,
        "vertex_count": len(source),
        "triangle_count": len(left),
        "winding": winding,
        "within_ds_vertex_budget": len(source) <= DS_VERTEX_LIMIT,
        "within_ds_triangle_budget": len(left) <= DS_TRIANGLE_LIMIT,
        "independent_original_3ds_provenance_verified": False,
        "native_ds_rendering_verified": False,
    }


def parse_obj(text):
    """Read one private, triangle-only OBJ mesh (positive global vertex indices)."""
    vertices, faces = [], []
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "v":
            if len(parts) != 4:
                raise ValueError("OBJ vertex must contain XYZ")
            vertices.append([float(value) for value in parts[1:]])
            if len(vertices) > MAX_VERTICES:
                raise ValueError("OBJ vertex budget exceeded")
        elif parts[0] == "f":
            if len(parts) != 4:
                raise ValueError("OBJ must be triangulated")
            face = []
            for token in parts[1:]:
                number = token.split("/")[0]
                if not number.isdecimal() or int(number) == 0:
                    raise ValueError("OBJ requires positive face indices")
                face.append(int(number) - 1)
            faces.append(face)
            if len(faces) > MAX_TRIANGLES:
                raise ValueError("OBJ triangle budget exceeded")
    _vertices(vertices)
    _faces(faces, len(vertices))
    return vertices, faces


def _private_input(path):
    resolved = Path(path).expanduser().resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("private input must be outside the public repository")
    if not resolved.is_file() or resolved.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("private input missing or exceeds byte budget")
    return resolved


def run_private(source_json, reference_obj, report, tolerance=1e-5):
    source = json.loads(_private_input(source_json).read_text(encoding="utf-8"))
    reference = _private_input(reference_obj).read_text(encoding="utf-8")
    if set(source) != {"vertices", "triangles"}:
        raise ValueError("source must contain exactly vertices and triangles")
    xyz, faces = parse_obj(reference)
    result = verify_mesh(source["vertices"], source["triangles"], xyz, faces,
                         tolerance=tolerance)
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
    print(f"C228 reference face coverage: {result['triangle_count']} triangles; "
          f"DS triangle budget: {result['within_ds_triangle_budget']}")


if __name__ == "__main__":
    main()
