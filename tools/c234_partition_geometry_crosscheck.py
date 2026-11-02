#!/usr/bin/env python3
"""C234: private, ordered mesh-partition geometric equivalence gate.

A whole-model triangle multiset can match even when its mesh/material partitions
have been interchanged. C234 compares source mesh i only with OBJ group i.
This is geometric evidence, not original primitive or material provenance.
"""
import argparse
import json
from pathlib import Path

from c180_private_c5_coverage import write_private_report
from c228_reference_topology_crosscheck import (
    DS_TRIANGLE_LIMIT, DS_VERTEX_LIMIT, MAX_TRIANGLES, MAX_VERTICES,
    _faces, _private_input, _vertices, parse_obj,
)
from c233_seam_geometry_crosscheck import verify_geometric_mesh

MAX_MESHES = 64


def parse_partitioned_obj(text):
    """Parse triangulated OBJ and retain contiguous o/g-delimited face groups.

    Mesh labels are intentionally neither trusted as IDs nor emitted in reports.
    An OBJ with no groups is exactly one mesh. Mixed o/g boundaries are kept
    as explicit separate partitions, rather than silently merging meshes.
    """
    vertices, faces = parse_obj(text)
    groups, current = [], []
    face_index = 0
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] in ("o", "g"):
            if len(parts) != 2 or len(parts[1]) > 128:
                raise ValueError("invalid OBJ partition declaration")
            if current:
                groups.append(current)
                current = []
            elif groups:
                raise ValueError("empty OBJ partition")
            if len(groups) >= MAX_MESHES:
                raise ValueError("OBJ mesh count exceeds budget")
        elif parts[0] == "f":
            current.append(faces[face_index])
            face_index += 1
    if not current:
        raise ValueError("empty OBJ partition")
    groups.append(current)
    if face_index != len(faces) or len(groups) > MAX_MESHES:
        raise ValueError("invalid OBJ partition coverage")
    return vertices, groups


def verify_partitioned_meshes(meshes, reference_vertices, reference_groups,
                              tolerance=1e-5):
    """Compare bounded source meshes with matching ordered reference partitions."""
    if (not isinstance(meshes, list) or not isinstance(reference_groups, list)
            or not 1 <= len(meshes) == len(reference_groups) <= MAX_MESHES):
        raise ValueError("mesh partition count mismatch or exceeds budget")
    reference = _vertices(reference_vertices)
    source_vertices = source_triangles = reference_triangles = 0
    reversed_meshes = seam_duplicates = 0
    for index, (mesh, group) in enumerate(zip(meshes, reference_groups)):
        if not isinstance(mesh, dict) or set(mesh) != {"vertices", "triangles"}:
            raise ValueError("invalid source mesh record")
        # Validate reference indices before remapping global OBJ IDs.
        checked = _faces(group, len(reference))
        used = sorted({vertex for face in checked for vertex in face})
        remap = {global_id: local_id for local_id, global_id in enumerate(used)}
        local_xyz = [reference[vertex] for vertex in used]
        local_faces = [[remap[vertex] for vertex in face] for face in checked]
        try:
            result = verify_geometric_mesh(
                mesh["vertices"], mesh["triangles"], local_xyz, local_faces,
                tolerance=tolerance)
        except ValueError as exc:
            raise ValueError("mesh partition %d: %s" % (index, exc)) from exc
        source_vertices += result["source_vertex_count"]
        source_triangles += result["triangle_count"]
        reference_triangles += len(checked)
        reversed_meshes += result["winding"] == "globally_reversed"
        seam_duplicates += result["source_seam_duplicate_vertices"]
        if source_vertices > MAX_VERTICES or source_triangles > MAX_TRIANGLES:
            raise ValueError("whole-model geometry exceeds validation budget")
    if source_triangles != reference_triangles:
        raise ValueError("mesh partition triangle count mismatch")
    return {
        "schema": "p3d-c234-private-partitioned-geometry-gate-v1",
        "ordered_mesh_partition_geometric_equivalence_verified": True,
        "original_mesh_identity_verified": False,
        "original_3ds_primitive_provenance_verified": False,
        "original_material_or_uv_bindings_verified": False,
        "native_ds_rendering_verified": False,
        "mesh_count": len(meshes),
        "source_vertex_count": source_vertices,
        "reference_vertex_count": len(reference),
        "triangle_count": source_triangles,
        "source_seam_duplicate_vertices": seam_duplicates,
        "globally_reversed_meshes": reversed_meshes,
        "within_ds_mesh_budget": len(meshes) <= MAX_MESHES,
        "within_ds_vertex_budget": source_vertices <= DS_VERTEX_LIMIT,
        "within_ds_triangle_budget": source_triangles <= DS_TRIANGLE_LIMIT,
    }


def run_private(source_json, reference_obj, report, tolerance=1e-5):
    source = json.loads(_private_input(source_json).read_text(encoding="utf-8"))
    if not isinstance(source, dict) or set(source) != {"meshes"}:
        raise ValueError("source JSON must contain only meshes")
    xyz, groups = parse_partitioned_obj(
        _private_input(reference_obj).read_text(encoding="utf-8"))
    result = verify_partitioned_meshes(source["meshes"], xyz, groups, tolerance)
    write_private_report(Path(report), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", required=True, type=Path)
    parser.add_argument("--reference-obj", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--tolerance", default=1e-5, type=float)
    args = parser.parse_args()
    result = run_private(args.source_json, args.reference_obj, args.report,
                         tolerance=args.tolerance)
    print("C234 partitioned geometric match:", result["mesh_count"],
          "meshes;", result["triangle_count"],
          "triangles; original primitive provenance verified: False")


if __name__ == "__main__":
    main()
