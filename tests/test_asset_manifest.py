import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_original_assets import validate

class TestAssetValidation(unittest.TestCase):
    def test_present_missing_changed_and_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pokemon").mkdir()
            file = root / "pokemon" / "test.dat"
            file.write_bytes(b"fixture, not game data")
            record = {
                "path": "pokemon/test.dat",
                "size": file.stat().st_size,
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest()
            }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "format": "p3d-ds-original-assets-v1",
                "assets": [record]
            }))
            self.assertEqual(validate(manifest, root), [])
            file.write_bytes(b"changed")
            self.assertTrue(validate(manifest, root))
            file.unlink()
            self.assertIn("Missing required original asset", " ".join(validate(manifest, root)))
            record["path"] = "../outside.dat"
            manifest.write_text(json.dumps({
                "format": "p3d-ds-original-assets-v1",
                "assets": [record]
            }))
            self.assertIn("Unsafe asset path", " ".join(validate(manifest, root)))

if __name__ == "__main__":
    unittest.main()
