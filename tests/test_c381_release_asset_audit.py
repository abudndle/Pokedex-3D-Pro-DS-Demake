"""Synthetic-only checks for UI release inventory."""
import tempfile
import unittest
from pathlib import Path
from tools.audit_ui_release_assets import FRAME_BYTES, REQUIRED, inspect


class ReleaseAssetAuditTests(unittest.TestCase):
    def test_missing_files_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect(tmp)
            self.assertEqual(report["missing"], len(REQUIRED))
            self.assertFalse(report["authenticity_verified"])

    def test_invalid_screen_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / REQUIRED[0]
            path.parent.mkdir(parents=True)
            path.write_bytes(b"bad")
            report = inspect(tmp)
            self.assertEqual(report["items"][0]["status"], "invalid_size")

    def test_correct_size_is_not_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / REQUIRED[0]
            path.parent.mkdir(parents=True)
            path.write_bytes(bytes(FRAME_BYTES))
            report = inspect(tmp)
            self.assertEqual(report["items"][0]["status"], "size_valid_needs_provenance_verification")
            self.assertFalse(report["authenticity_verified"])


if __name__ == "__main__":
    unittest.main()
