"""C233 synthetic-only UV-seam geometric equivalence and safety regressions."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c233_seam_geometry_crosscheck import verify_geometric_mesh, run_private

XYZ = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
FACES = [[0, 1, 2], [0, 2, 3]]


class C233SeamGeometryTests(unittest.TestCase):
    def test_strict_mesh_still_matches_geometrically(self):
        result = verify_geometric_mesh(XYZ, FACES, XYZ, FACES)
        self.assertTrue(result["geometric_face_equivalence_verified"])
        self.assertFalse(result["exact_index_topology_verified"])
        self.assertFalse(result["independent_original_3ds_provenance_verified"])
        self.assertEqual(result["winding"], "same")

    def test_uv_seam_duplicate_and_different_vertex_counts(self):
        source = XYZ + [[0, 0, 0]]
        result = verify_geometric_mesh(source, [[0, 1, 2], [4, 2, 3]], XYZ, FACES)
        self.assertEqual(result["source_seam_duplicate_vertices"], 1)
        self.assertEqual(result["reference_seam_duplicate_vertices"], 0)
        self.assertEqual(result["unique_position_classes"], 4)
        self.assertFalse(result["uv_seam_vertex_identity_verified"])

    def test_reference_seam_and_reordered_vertices(self):
        reference = [XYZ[2], XYZ[0], XYZ[3], XYZ[1], XYZ[0]]
        result = verify_geometric_mesh(XYZ, FACES, reference,
                                       [[4, 3, 0], [1, 0, 2]])
        self.assertEqual(result["reference_seam_duplicate_vertices"], 1)
        self.assertEqual(result["winding"], "same")

    def test_globally_reversed_winding(self):
        result = verify_geometric_mesh(XYZ, FACES, XYZ,
                                       [[2, 1, 0], [3, 2, 0]])
        self.assertEqual(result["winding"], "globally_reversed")

    def test_mixed_winding_rejected(self):
        with self.assertRaisesRegex(ValueError, "winding"):
            verify_geometric_mesh(XYZ, FACES, XYZ, [[0, 1, 2], [3, 2, 0]])

    def test_wrong_topology_rejected(self):
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            verify_geometric_mesh(XYZ, FACES, XYZ, [[0, 1, 3], [1, 2, 3]])

    def test_distinct_nearby_reference_classes_are_ambiguous(self):
        reference = [[0, 0, 0], [0.000001, 0, 0], [1, 0, 0], [0, 1, 0]]
        with self.assertRaisesRegex(ValueError, "ambiguous distinct reference"):
            verify_geometric_mesh(reference, FACES, reference, FACES)

    def test_geometric_degeneracy_after_seam_collapse_rejected(self):
        source = [[0, 0, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0]]
        with self.assertRaisesRegex(ValueError, "geometrically degenerate"):
            verify_geometric_mesh(source, [[0, 1, 2]],
                                  [XYZ[0], XYZ[1], XYZ[3]], [[0, 1, 2]])

    def test_private_report_is_0600_and_excludes_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            obj = root / "reference.obj"
            report = root / "report.json"
            source.write_text(json.dumps({"vertices": XYZ, "triangles": FACES}))
            obj.write_text("".join(f"v {x} {y} {z}\n" for x, y, z in XYZ) +
                           "f 1 2 3\nf 1 3 4\n")
            result = run_private(source, obj, report)
            self.assertEqual(os.stat(report).st_mode & 0o777, 0o600)
            payload = json.loads(report.read_text())
            self.assertEqual(payload, result)
            self.assertNotIn("vertices", payload)
            self.assertNotIn("triangles", payload)

    def test_invalid_tolerance_and_missing_classes(self):
        for tolerance in (0, -1, float("nan"), 0.1, True):
            with self.assertRaisesRegex(ValueError, "tolerance"):
                verify_geometric_mesh(XYZ, FACES, XYZ, FACES, tolerance)
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            verify_geometric_mesh(XYZ, [[0, 1, 2]], XYZ + [[2, 2, 2]],
                                  [[0, 1, 2]])


if __name__ == "__main__":
    unittest.main()
