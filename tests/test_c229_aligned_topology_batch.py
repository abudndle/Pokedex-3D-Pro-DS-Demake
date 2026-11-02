"""C229 synthetic-only strict triangle-prefix and alignment regressions."""
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c227_private_topology_batch import find_topology
from c229_aligned_topology_batch import (
    audit_archives, find_aligned_candidate, recover_candidate,
)


def aligned_two_mesh_c5():
    """Three triangles on first mesh require a 2-byte pad before mesh 2."""
    data = bytearray(348)
    data[:2] = b"\xc5\x78"
    struct.pack_into("<3H", data, 0x14, 2, 2, 0)
    struct.pack_into("<5I", data, 0x3C, 120, 160, 184, 184, 184)
    struct.pack_into("<5I", data, 120, 184, 0, 4 | (12 << 16), 0, 0)
    struct.pack_into("<5I", data, 140, 232, 0, 4 | (12 << 16), 0, 0)
    struct.pack_into("<3I", data, 160, 280, 0, 9 | (2 << 16))
    struct.pack_into("<3I", data, 172, 300, 0, 6 | (2 << 16))
    # The first mesh intentionally does not start with the C227 quad signature.
    struct.pack_into("<9H", data, 316, 0, 1, 2, 1, 2, 3, 1, 3, 0)
    # Two alignment bytes at offsets 334..335, then mesh 2 at 336.
    struct.pack_into("<6H", data, 336, 0, 1, 2, 0, 2, 3)
    return bytes(data)


def legacy_one_mesh_c5():
    data = bytearray(288)
    data[:2] = b"\xc5\x78"
    struct.pack_into("<3H", data, 0x14, 1, 1, 0)
    struct.pack_into("<5I", data, 0x3C, 120, 140, 152, 152, 152)
    struct.pack_into("<5I", data, 120, 152, 0, 4 | (28 << 16), 0, 0)
    struct.pack_into("<3I", data, 140, 264, 0, 6 | (2 << 16))
    struct.pack_into("<6H", data, 264, 0, 1, 2, 0, 2, 3)
    struct.pack_into("<6H", data, 276, 0, 1, 2, 0, 2, 3)
    return bytes(data)


def make_archives(directory, data):
    for part in (1, 2, 3):
        with zipfile.ZipFile(
            directory / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w"
        ) as archive:
            for value in range((part - 1) * 250, min(part * 250, 734)):
                if value not in (721, 722, 723, 724):
                    archive.writestr(f"decoded_c5/p{value:03d}.c5", data)


class C229AlignedRecoveryTests(unittest.TestCase):
    def test_alignment_fixes_synthetic_mesh_stream(self):
        source = aligned_two_mesh_c5()
        with self.assertRaisesRegex(ValueError, "unique fully validated"):
            find_topology(source, "p000")
        recovered = recover_candidate(source, "p000")
        self.assertEqual(recovered["candidate_method"],
                         "c229-triangle-prefix-four-byte-aligned")
        self.assertEqual((recovered["mesh_count"], recovered["vertex_count"],
                          recovered["triangle_count"]), (2, 8, 5))
        self.assertEqual(recovered["meshes"][0]["triangles"],
                         [[0, 1, 2], [1, 2, 3], [1, 3, 0]])
        self.assertEqual(recovered["meshes"][1]["triangles"],
                         [[0, 1, 2], [0, 2, 3]])
        self.assertFalse(recovered["independent_topology_provenance_verified"])

    def test_prior_c227_candidate_is_kept_unchanged(self):
        source = legacy_one_mesh_c5()
        old = find_topology(source, "p010")
        recovered = recover_candidate(source, "p010")
        self.assertEqual(recovered["candidate_method"], "c227-quad-prefix-contiguous")
        self.assertEqual(recovered["topology_start"], old["topology_start"])
        self.assertEqual(recovered["meshes"], old["meshes"])

    def test_ambiguous_multiple_aligned_regions_rejected(self):
        source = aligned_two_mesh_c5()
        double = source + source[316:]
        with self.assertRaisesRegex(ValueError, "one aligned C5 topology candidate"):
            find_aligned_candidate(double, "p000")

    def test_wrong_index_fails_closed(self):
        source = bytearray(aligned_two_mesh_c5())
        struct.pack_into("<H", source, 340, 99)
        with self.assertRaises(ValueError):
            find_aligned_candidate(bytes(source), "p000")

    def test_corrupt_header_fails_closed(self):
        source = bytearray(aligned_two_mesh_c5())
        source[:2] = b"ZZ"
        with self.assertRaisesRegex(ValueError, "not a C5"):
            recover_candidate(bytes(source), "p000")

    def test_synthetic_730_record_private_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archives = root / "private-c56"
            archives.mkdir()
            make_archives(archives, aligned_two_mesh_c5())
            output = root / "private-results"
            result = audit_archives(archives, output)
            self.assertEqual(result["source_model_records_checked"], 730)
            self.assertEqual(result["c227_preserved_candidates"], 0)
            self.assertEqual(result["c229_additional_aligned_candidates"], 730)
            self.assertEqual(result["combined_candidate_models"], 730)
            self.assertEqual(result["unresolved_records"], 0)
            self.assertFalse(result["independent_topology_provenance_verified"])
            self.assertEqual(len(list((output / "topology").glob("p*.json"))), 730)
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o700)
            self.assertEqual(os.stat(output / "summary.json").st_mode & 0o777, 0o600)
            self.assertEqual(json.loads((output / "summary.json").read_text()),
                             result)
            with self.assertRaisesRegex(ValueError, "must not already exist"):
                audit_archives(archives, output)


if __name__ == "__main__":
    unittest.main()
