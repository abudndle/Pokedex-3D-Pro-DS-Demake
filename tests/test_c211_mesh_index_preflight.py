"""Synthetic, asset-free tests for C211 mesh-local index preflight."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import struct
import zlib
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("c211", ROOT / "tools/c211_mesh_index_preflight.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class MeshPreflightTests(unittest.TestCase):
    def pair(self, root, index=(0, 1, 2), vertex_count=3, mesh=0):
        payload = struct.pack("<HHI", mesh, vertex_count, 0) + b"\0" * (vertex_count * 6)
        vx = b"P3VX" + struct.pack("<HHHHI", 1, 14, 1, 0, zlib.crc32(payload)) + payload
        ix = b"P3IX" + struct.pack("<HHH", 1, 14, 1)
        ix += struct.pack("<HI3H", mesh, 1, *index)
        vp, ip = Path(root) / "p014.p3vx", Path(root) / "p014.p3ix"
        vp.write_bytes(vx)
        ip.write_bytes(ix)
        return vp, ip

    def test_valid_mesh_local_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp, (0, 1, 2), 3)
            self.assertEqual(mod.inspect_pair(vp, ip, 14), 1)

    def test_global_valid_but_mesh_local_out_of_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp, (0, 1, 3), 3)
            with self.assertRaisesRegex(ValueError, "mesh-local"):
                mod.inspect_pair(vp, ip, 14)

    def test_duplicate_vertex_mesh_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp)
            payload = (struct.pack("<HHI", 0, 3, 0)
                       + struct.pack("<HHI", 0, 3, 3) + bytes(36))
            vp.write_bytes(b"P3VX" + struct.pack("<HHHHI", 1, 14, 2, 0, zlib.crc32(payload)) + payload)
            with self.assertRaisesRegex(ValueError, "vertex mesh order"):
                mod.inspect_pair(vp, ip, 14)

    def test_index_roster_must_cover_every_vertex_mesh(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp)
            payload = (struct.pack("<HHI", 0, 3, 0)
                       + struct.pack("<HHI", 1, 3, 3) + bytes(36))
            vp.write_bytes(b"P3VX" + struct.pack("<HHHHI", 1, 14, 2, 0, zlib.crc32(payload)) + payload)
            with self.assertRaisesRegex(ValueError, "rosters differ"):
                mod.inspect_pair(vp, ip, 14)

    def test_degenerate_triangle(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp, (0, 0, 2), 3)
            with self.assertRaisesRegex(ValueError, "degenerate"):
                mod.inspect_pair(vp, ip, 14)

    def test_oversized_vertex_file_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp)
            with vp.open("ab") as file:
                file.truncate(mod.MAX_VERTEX_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "oversized vertex"):
                mod.inspect_pair(vp, ip, 14)

    def test_oversized_index_file_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp)
            with ip.open("ab") as file:
                file.truncate(mod.MAX_INDEX_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "oversized index"):
                mod.inspect_pair(vp, ip, 14)

    def test_corrupted_vertex_crc(self):
        with tempfile.TemporaryDirectory() as tmp:
            vp, ip = self.pair(tmp)
            raw = bytearray(vp.read_bytes())
            raw[-1] ^= 1
            vp.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "CRC"):
                mod.inspect_pair(vp, ip, 14)

if __name__ == "__main__":
    unittest.main()
