"""Regression tests for the public port readiness inventory."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("readiness", ROOT / "tools/check_port_readiness.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ReadinessTests(unittest.TestCase):
    def test_current_repository_has_required_public_inputs(self):
        result = mod.check(ROOT)
        self.assertEqual(result["missing_public_files"], [])
        self.assertTrue(result["public_source_complete"])
        self.assertFalse(result["full_original_port_verified"])

    def test_missing_public_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.check(tmp)
        self.assertFalse(result["public_source_complete"])
        self.assertIn("Makefile.native", result["missing_public_files"])
        self.assertFalse(result["full_original_port_verified"])

    def test_private_original_resource_gates_are_not_claimed(self):
        result = mod.check(ROOT)
        self.assertGreaterEqual(len(result["private_original_asset_gates"]), 5)
        self.assertTrue(all(not gate["verified"] for gate in result["private_original_asset_gates"]))

if __name__ == "__main__":
    unittest.main()
