"""C227 synthetic-only regressions for strict original C5 topology recovery."""
import struct
import json
import os
import tempfile
import zipfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c227_private_topology_batch import find_topology, inspect_faces, audit_archives


def quad_c5():
    # One mesh: four 28-byte vertex records, six descriptor u16s, then the
    # independently validated (0,1,2),(0,2,3) topology signature and indices.
    data = bytearray(288)
    data[:2] = b"\xc5\x78"
    struct.pack_into("<3H", data, 0x14, 1, 1, 0)
    struct.pack_into("<5I", data, 0x3c, 120, 140, 152, 152, 152)
    struct.pack_into("<5I", data, 120, 152, 0, 4 | (28 << 16), 0, 0)
    struct.pack_into("<3I", data, 140, 264, 0, 6 | (2 << 16))
    # Descriptor candidate payload is distinct from the recovered index stream.
    struct.pack_into("<6H", data, 264, 0, 1, 2, 0, 2, 3)
    struct.pack_into("<6H", data, 276, 0, 1, 2, 0, 2, 3)
    return bytes(data)


def make_archives(directory, missing=None, duplicate=False):
    missing = set(missing or ())
    for part in (1, 2, 3):
        with zipfile.ZipFile(directory / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as archive:
            for model in range((part - 1) * 250, min(part * 250, 734)):
                if model in (721, 722, 723, 724) or model in missing:
                    continue
                name = f"decoded_c5/p{model:03d}.c5"
                archive.writestr(name, quad_c5())
                if duplicate and model == 0:
                    archive.writestr(name, quad_c5())


class C227TopologyTests(unittest.TestCase):
    def test_real_archive_member_pattern(self):
        from c227_private_topology_batch import MODEL_MEMBER
        self.assertIsNotNone(MODEL_MEMBER.fullmatch("decoded_c5/p000.c5"))
        self.assertIsNotNone(MODEL_MEMBER.fullmatch("decoded_c5/p733.c5"))
        self.assertIsNone(MODEL_MEMBER.fullmatch("decoded_c5/p000.c5.bak"))
        self.assertIsNone(MODEL_MEMBER.fullmatch("decoded_c5/p000.c5\\\\Z"))

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

    def test_full_synthetic_roster_private_atomic_report(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            archives = base / "source"
            archives.mkdir()
            make_archives(archives)
            output = base / "private-report"
            result = audit_archives(archives, output)
            self.assertEqual(result["c5_models_audited"], 730)
            self.assertEqual(result["models_with_strict_topology"], 730)
            self.assertFalse(result["independent_topology_provenance_verified"])
            self.assertEqual(len(list((output / "topology").glob("*.json"))), 730)
            self.assertEqual(json.loads((output / "summary.json").read_text())["c5_models_audited"], 730)
            self.assertTrue((output / "summary.json").read_bytes().endswith(b"\n"))
            self.assertEqual(os.stat(output / "summary.json").st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o700)
            with self.assertRaisesRegex(ValueError, "must not already exist"):
                audit_archives(archives, output)

    def test_incomplete_roster_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            archives = base / "source"
            archives.mkdir()
            make_archives(archives, missing={0})
            output = base / "private-report"
            with self.assertRaisesRegex(ValueError, "roster"):
                audit_archives(archives, output)
            self.assertFalse(output.exists())

    def test_duplicate_zip_member_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            archives = base / "source"
            archives.mkdir()
            make_archives(archives, duplicate=True)
            output = base / "private-report"
            with self.assertRaisesRegex(ValueError, "duplicate ZIP member"):
                audit_archives(archives, output)
            self.assertFalse(output.exists())

    def test_bad_c5_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a C5"):
            find_topology(b"not a C5 file")


if __name__ == "__main__":
    unittest.main()
