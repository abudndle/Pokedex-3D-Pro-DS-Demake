"""C179 asset-free end-to-end synthetic test of the actual native GL draw path."""
import pathlib
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests/run_c179_private_geometry_draw_probe.sh"

class GeometryDrawProbeTest(unittest.TestCase):
    def test_verified_pair_draw_and_corruption(self):
        model = 14
        mesh = struct.pack("<HHI", 7, 3, 0)
        xyz = struct.pack("<9h", 100, 101, 102, 200, 201, 202, 300, 301, 302)
        payload = mesh + xyz
        vx = struct.pack("<4sHHHHI", b"P3VX", 1, model, 1, 0, zlib.crc32(payload)) + payload
        ix = struct.pack("<4sHHHHI3H", b"P3IX", 1, model, 1, 7, 1, 0, 1, 2)
        with tempfile.TemporaryDirectory() as d:
            vertex = pathlib.Path(d) / "p014.p3vx"
            index = pathlib.Path(d) / "p014.p3ix"
            vertex.write_bytes(vx)
            index.write_bytes(ix)
            command = ["sh", str(RUNNER), str(vertex), str(index), str(model), "1"]
            success = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertIn("native GL path OK", success.stdout)
            index.write_bytes(ix[:-1])
            failure = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)
            index.write_bytes(ix)
            wrong = subprocess.run(command[:-1] + ["2"], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(wrong.returncode, 0)

if __name__ == "__main__":
    unittest.main()
