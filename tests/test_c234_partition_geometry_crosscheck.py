"""C234 synthetic-only partitioned geometry and private reporting regressions."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c234_partition_geometry_crosscheck import (
    parse_partitioned_obj, run_private, verify_partitioned_meshes,
)
from c233_seam_geometry_crosscheck import verify_geometric_mesh

XYZ = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
TRI_A = [[0, 1, 2]]
TRI_B = [[0, 2, 3]]
OBJ = ("v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\n"
       "g front\nf 1 2 3\ng back\nf 1 3 4\n")
MESHES = [
    {"vertices": XYZ, "triangles": TRI_A},
    {"vertices": XYZ, "triangles": TRI_B},
]


class C234PartitionTests(unittest.TestCase):
    def test_two_meshes_match_and_claims_remain_bounded(self):
        vertices, groups = parse_partitioned_obj(OBJ)
        report = verify_partitioned_meshes(MESHES, vertices, groups)
        self.assertTrue(report["ordered_mesh_partition_geometric_equivalence_verified"])
        self.assertFalse(report["original_mesh_identity_verified"])
        self.assertFalse(report["original_3ds_primitive_provenance_verified"])
        self.assertEqual(report["mesh_count"], 2)
        self.assertEqual(report["triangle_count"], 2)

    def test_whole_model_false_positive_is_rejected_by_partition_gate(self):
        vertices, groups = parse_partitioned_obj(OBJ)
        swapped = [MESHES[1], MESHES[0]]
        self.assertTrue(verify_geometric_mesh(
            XYZ, TRI_A + TRI_B, XYZ, TRI_A + TRI_B
        )["geometric_face_equivalence_verified"])
        with self.assertRaisesRegex(ValueError, "mesh partition 0"):
            verify_partitioned_meshes(swapped, vertices, groups)

    def test_seams_and_reversed_winding_within_partition(self):
        vertices, groups = parse_partitioned_obj(OBJ)
        quad_obj = ("v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\n"
                    "g quad\nf 1 2 3\nf 1 3 4\n"
                    "g other\nf 1 3 4\n")
        seam = [{"vertices": XYZ + [XYZ[0]],
                 "triangles": [[0, 1, 2], [4, 2, 3]]},
                {"vertices": XYZ, "triangles": [[3, 2, 0]]}]
        quad_xyz, quad_groups = parse_partitioned_obj(quad_obj)
        report = verify_partitioned_meshes(seam, quad_xyz, quad_groups)
        self.assertEqual(report["source_seam_duplicate_vertices"], 1)
        self.assertEqual(report["globally_reversed_meshes"], 1)

    def test_partition_count_and_missing_groups(self):
        vertices, groups = parse_partitioned_obj(OBJ)
        with self.assertRaisesRegex(ValueError, "partition count"):
            verify_partitioned_meshes(MESHES[:1], vertices, groups)
        single_xyz, single_groups = parse_partitioned_obj(
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
        self.assertEqual(len(single_groups), 1)
        with self.assertRaisesRegex(ValueError, "partition count"):
            verify_partitioned_meshes(MESHES, single_xyz, single_groups)

    def test_invalid_or_empty_obj_group_fails_closed(self):
        for data in (OBJ + "g empty\n", OBJ.replace("g back", "g two words"),
                     OBJ + "g tail\ng tail2\n"):
            with self.assertRaises(ValueError):
                parse_partitioned_obj(data)

    def test_bad_reference_indices_and_source_schema(self):
        with self.assertRaises(ValueError):
            verify_partitioned_meshes(MESHES, XYZ, [[[0, 1, 99]], TRI_B])
        with self.assertRaises(ValueError):
            verify_partitioned_meshes([{"vertices": XYZ, "triangles": TRI_A,
                                        "original": "untrusted"}], XYZ, [TRI_A])

    def test_private_input_and_0600_report_no_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, obj, report = (root / "source.json", root / "reference.obj",
                                   root / "report.json")
            source.write_text(json.dumps({"meshes": MESHES}))
            obj.write_text(OBJ)
            result = run_private(source, obj, report)
            self.assertEqual(json.loads(report.read_text()), result)
            self.assertEqual(os.stat(report).st_mode & 0o777, 0o600)
            self.assertNotIn('"vertices":', json.dumps(result))
            self.assertNotIn('"triangles":', json.dumps(result))
            self.assertNotIn("front", json.dumps(result))

    def test_invalid_tolerance_and_geometry_fail_closed(self):
        vertices, groups = parse_partitioned_obj(OBJ)
        with self.assertRaisesRegex(ValueError, "tolerance"):
            verify_partitioned_meshes(MESHES, vertices, groups, tolerance=0)
        bad = [{"vertices": XYZ, "triangles": TRI_A},
               {"vertices": XYZ, "triangles": TRI_A}]
        with self.assertRaisesRegex(ValueError, "mesh partition 1"):
            verify_partitioned_meshes(bad, vertices, groups)


if __name__ == "__main__":
    unittest.main()
