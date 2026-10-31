import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("inspect_ds3m", Path(__file__).resolve().parents[1] / "tools" / "inspect_ds3m.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class DS3MTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "p000.ds3m"

    def write(self, version, count, payload=None):
        if payload is None:
            payload = bytes(count * 18 + (count * 3 if version == 2 else 0))
        self.file.write_bytes(struct.pack("<4sHHII", b"DS3M", version, count, 0, count) + payload)

    def test_v1(self):
        self.write(1, 1)
        self.assertEqual(mod.inspect(self.file)["triangles"], 1)

    def test_v2_boundary(self):
        self.write(2, 600)
        self.assertEqual(mod.inspect(self.file)["version"], 2)

    def test_over_capacity(self):
        self.write(1, 601)
        with self.assertRaisesRegex(ValueError, "budget"):
            mod.inspect(self.file)

    def test_truncated_color(self):
        self.write(2, 1, bytes(18))
        with self.assertRaisesRegex(ValueError, "length"):
            mod.inspect(self.file)

    def test_trailing_bytes(self):
        self.write(1, 1, bytes(19))
        with self.assertRaisesRegex(ValueError, "length"):
            mod.inspect(self.file)

    def test_bad_magic(self):
        self.write(1, 1)
        data = bytearray(self.file.read_bytes())
        data[:4] = b"BAD!"
        self.file.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "magic"):
            mod.inspect(self.file)

if __name__ == "__main__":
    unittest.main()
