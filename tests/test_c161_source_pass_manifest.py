"""C161 synthetic manifest tests; no original assets."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from c161_source_pass_manifest import build_manifest
from test_c160_draw_pass_contract import fixture

class C161ManifestTests(unittest.TestCase):
    def test_secondary_only_preserved(self):
        m = build_manifest("p188", fixture(mode=0x0c01))
        self.assertEqual(m["secondary_only_meshes"], [0])
        self.assertEqual(m["draws"][0]["pass"], "secondary")
        self.assertFalse(m["sampler_roles_verified"])
        self.assertFalse(m["native_renderer_integrated"])
    def test_primary_preserved(self):
        m = build_manifest("p659", fixture())
        self.assertEqual(m["secondary_only_meshes"], [])
        self.assertEqual(m["draws"][0]["material"], 0)
        self.assertEqual(m["draws"][0]["pass"], "primary")
    def test_invalid_model_rejected(self):
        for name in ("p721", "p999", "../p188", "p188.c5"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build_manifest(name, fixture())
    def test_invalid_source_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest("p188", b"not a C5")

if __name__ == "__main__":
    unittest.main()
