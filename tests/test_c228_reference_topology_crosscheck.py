"""C228 synthetic-only original-reference triangle equivalence regressions."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c228_reference_topology_crosscheck import parse_obj, run_private, verify_mesh

XYZ = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
FACES = [[0, 1, 2], [0, 2, 3]]


class C228ReferenceTopologyTests(unittest.TestCase):
    def test_exact_triangle_coverage(self):
        result = verify_mesh(XYZ, FACES, XYZ, FACES)
        self.assertTrue(result["reference_face_equivalence_verified"])
        self.assertEqual(result["winding"], "same")
        self.assertTrue(result["within_ds_triangle_budget"])
        self.assertFalse(result["independent_original_3ds_provenance_verified"])
        self.assertFalse(result["native_ds_rendering_verified"])

    def test_reordered_vertices_and_rotated_faces(self):
        reference = [XYZ[2], XYZ[0], XYZ[3], XYZ[1]]
        faces = [[1, 3, 0], [1, 0, 2]]
        self.assertEqual(verify_mesh(XYZ, FACES, reference, faces)["winding"], "same")

    def test_globally_reversed_winding_is_explicit(self):
        reversed_faces = [[2, 1, 0], [3, 2, 0]]
        self.assertEqual(verify_mesh(XYZ, FACES, XYZ, reversed_faces)["winding"],
                         "globally_reversed")

    def test_mixed_winding_rejected(self):
        with self.assertRaisesRegex(ValueError, "winding"):
            verify_mesh(XYZ, FACES, XYZ, [[0, 1, 2], [3, 2, 0]])

    def test_different_face_topology_rejected(self):
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            verify_mesh(XYZ, FACES, XYZ, [[0, 1, 3], [1, 2, 3]])

    def test_duplicate_coordinate_ambiguity_rejected(self):
        xyz = [[0, 0, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0]]
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            verify_mesh(xyz, FACES, xyz, FACES)

    def test_out_of_range_and_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, "out-of-range"):
            verify_mesh(XYZ, [[0, 1, 4]], XYZ, FACES)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            verify_mesh([[float("nan"), 0, 0]] + XYZ[1:], FACES, XYZ, FACES)

    def test_obj_parser_and_bad_face_forms(self):
        obj = "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1/2/3 2/2/3 3/2/3\n"
        vertices, faces = parse_obj(obj)
        self.assertEqual((len(vertices), faces), (3, [[0, 1, 2]]))
        with self.assertRaisesRegex(ValueError, "triangulated"):
            parse_obj(obj.replace("f 1/2/3 2/2/3 3/2/3",
                                  "f 1 2 3 1"))
        with self.assertRaisesRegex(ValueError, "positive"):
            parse_obj(obj.replace("f 1/2/3", "f -1/2/3"))

    def test_private_cli_report_is_0600_and_has_no_original_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            obj = root / "reference.obj"
            report = root / "report.json"
            source.write_text(json.dumps({"vertices": XYZ, "triangles": FACES}))
            obj.write_text("".join(f"v {x} {y} {z}\n" for x, y, z in XYZ) +
                           "f 1 2 3\nf 1 3 4\n")
            result = run_private(source, obj, report)
            self.assertTrue(result["reference_face_equivalence_verified"])
            self.assertEqual(os.stat(report).st_mode & 0o777, 0o600)
            payload = json.loads(report.read_text())
            self.assertNotIn("vertices", payload)
            self.assertNotIn("triangles", payload)
            self.assertEqual(payload["triangle_count"], 2)


if __name__ == "__main__":
    unittest.main()
