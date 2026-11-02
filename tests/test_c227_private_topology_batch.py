"""C227 synthetic-only regressions for strict original C5 topology recovery."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c227_private_topology_batch import find_topology, inspect_faces


def quad_c5():
    # One mesh: four 28-byte vertex records, six descriptor u16s, then the
    # independently validated (0,1,2),(0,2,3) topology signature and indices.
    data = bytearray(288)
    data[:2] = b"\\xc5\\x78"
    struct.pack_into("<3H", data, 0x14, 1, 1, 0)
    struct.pack_into("<5I", data, 0x3c, 120, 140, 152, 152, 152)
    struct.pack_into("<5I", data, 120, 152, 0, 4 | (28 << 16), 0, 0)
    struct.pack_into("<3I", data, 140, 264, 0, 6 | (2 << 16))
    # Descriptor candidate payload is distinct from the recovered index stream.
    struct.pack_into("<6H", data, 264, 0, 1, 2, 0, 2, 3)
    struct.pack_into("<6H", data, 276, 0, 1, 2, 0, 2, 3)
    return bytes(data)


class C227TopologyTests(unittest.TestCase):
    def test_unique_topology_recovered(self):
        result = find_topology(quad_c5(), "p000")
        self.assertEqual((result["mesh_count"], result["vertex_count"],
                          result["triangle_count"]), (1, 4, 2))
        self.assertEqual(result["meshes"][0]["triangles"], [[0, 1, 2], [0, 2, 3]])
        self.assertFalse(result["complete_models_verified"])
        self.assertFalse(result["native_ds_rendering_verified"])

    def test_out_of_range_index_rejected(self):
        raw = bytearray(quad_c5())
        struct.pack_into("<H", raw, 284, 4)
        with self.assertRaisesRegex(ValueError, "unique fully validated"):
            find_topology(bytes(raw), "p000")

    def test_duplicate_triangle_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate triangle"):
            inspect_faces([0, 1, 2, 0, 1, 2], 3)

    def test_nonmanifold_edge_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-manifold"):
            inspect_faces([0, 1, 2, 1, 0, 3, 0, 1, 4], 5)

    def test_unreferenced_vertex_rejected(self):
        with self.assertRaisesRegex(ValueError, "not every source vertex"):
            inspect_faces([0, 1, 2], 4)

    def test_bad_c5_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a C5"):
            find_topology(b"not a C5 file")


if __name__ == "__main__":
    unittest.main()
