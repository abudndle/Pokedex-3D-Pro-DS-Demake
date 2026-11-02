"""Synthetic XWD regressions for C251 mapped/unmapped native ROM diagnostic."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c251_synthetic_geometry_frame_gate import compare_synthetic
from test_c235_emulator_frame_gate import make_xwd, paint_region


class C251GeometryFrameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="c251-frame-")
        self.addCleanup(self.tmp.cleanup)
        self.paths = [Path(self.tmp.name) / f"{name}.xwd"
                      for name in ("home", "mapped", "unmapped", "back")]
        for path, value in zip(self.paths, (0, 100, 100, 0)):
            make_xwd(path, value)
        paint_region(self.paths[2], (133, 38, 145, 49), 200)
        paint_region(self.paths[2], (86, 295, 96, 304), 200)

    def test_upper_center_change_is_diagnostic_not_original_proof(self):
        paint_region(self.paths[2], (100, 100, 120, 120), 200)
        result = compare_synthetic(*self.paths)
        self.assertGreater(result["mapped_vs_unmapped_upper_center_pixels"], 20)
        self.assertFalse(result["original_geometry_rendering_verified"])

    def test_two_number_glyph_changes_alone_not_geometry(self):
        with self.assertRaisesRegex(ValueError, "upper-screen region unchanged"):
            compare_synthetic(*self.paths)

    def test_missing_b_navigation_rejected(self):
        make_xwd(self.paths[3], 100)
        paint_region(self.paths[2], (100, 100, 120, 120), 200)
        with self.assertRaisesRegex(ValueError, "B did not"):
            compare_synthetic(*self.paths)

    def test_stale_preview_behind_home_rejected(self):
        paint_region(self.paths[2], (100, 100, 120, 120), 200)
        # A stale model can be small enough for the original B navigation
        # tolerance; the C252 upper-center gate must reject it explicitly.
        paint_region(self.paths[3], (115, 85, 130, 100), 200)
        with self.assertRaisesRegex(ValueError, "stale 3D preview"):
            compare_synthetic(*self.paths)


if __name__ == "__main__":
    unittest.main()
