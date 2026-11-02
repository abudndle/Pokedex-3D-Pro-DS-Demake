"""Synthetic-only C282 16-bit packed pixel candidate/ambiguity regression."""
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from c282_private_packed16_candidates import CANDIDATES, candidate_matches, morton8


def fixture(decode, width=8, height=8):
    source = bytearray(2 * width * height)
    p3px = bytearray(struct.pack("<4sHHH", b"P3PX", 2, width, height))
    for y in range(height):
        for x in range(width):
            word = (x * 9719 + y * 2903 + x * y * 163 + 1177) & 65535
            sy = height - 1 - y
            index = ((sy // 8) * (width // 8) + x // 8) * 64 + morton8(x % 8, sy % 8)
            struct.pack_into("<H", source, 2 * index, word)
            p3px += struct.pack("<H", decode(word))
    return bytes(source), bytes(p3px)


class C282Tests(unittest.TestCase):
    def test_all_candidate_layouts_detected(self):
        for name, decode in CANDIDATES.items():
            with self.subTest(name=name):
                source, p3px = fixture(decode)
                self.assertIn(name, candidate_matches(source, 8, 8, p3px))

    def test_stdlib_fallback_without_numpy(self):
        from unittest.mock import patch
        source, p3px = fixture(CANDIDATES["RGB565_R_HIGH"], 16, 8)
        with patch.dict(sys.modules, {"numpy": None}):
            self.assertEqual(candidate_matches(source, 16, 8, p3px),
                             ("RGB565_R_HIGH",))

    def test_two_tile_morton_and_vertical_flip(self):
        source, p3px = fixture(CANDIDATES["RGB565_R_HIGH"], 16, 8)
        self.assertEqual(candidate_matches(source, 16, 8, p3px), ("RGB565_R_HIGH",))

    def test_pixel_corruption_does_not_claim_match(self):
        source, p3px = fixture(CANDIDATES["RGBA5551_A_LOW"])
        broken = bytearray(p3px)
        broken[10] ^= 0x80
        self.assertEqual(candidate_matches(source, 8, 8, bytes(broken)), ())

    def test_uniform_source_reports_ambiguity(self):
        source = bytes(128)
        p3px = struct.pack("<4sHHH", b"P3PX", 2, 8, 8) + bytes(128)
        self.assertGreater(len(candidate_matches(source, 8, 8, p3px)), 1)

    def test_reject_invalid_dimensions_and_source_length(self):
        source, p3px = fixture(CANDIDATES["RGB565_R_HIGH"])
        for s, w, h in ((source[:-2], 8, 8), (source, 7, 8), (source, 8, 9), (source, 1024, 1024)):
            with self.assertRaisesRegex(ValueError, "size or tile"):
                candidate_matches(s, w, h, p3px)

    def test_reject_bad_p3px_header_length_and_version(self):
        source, p3px = fixture(CANDIDATES["RGB565_R_HIGH"])
        for broken in (p3px[:-1], b"bad", p3px[:4] + b"\x01\x00" + p3px[6:]):
            with self.assertRaisesRegex(ValueError, "header/dimensions/length"):
                candidate_matches(source, 8, 8, broken)


class C282SyntheticArchiveTests(unittest.TestCase):
    def run_audit(self, corrupt=False, mismatch_anchor=False):
        import hashlib
        import re
        import tempfile
        import types
        import zipfile
        from unittest.mock import patch
        from c282_private_packed16_candidates import audit
        source, p3px = fixture(CANDIDATES["RGB565_R_HIGH"])
        source_bytes = b"synthetic-header" + source
        start = len(b"synthetic-header")
        metadata = [{"byte_density": "16_BPP_STORAGE_ONLY", "source_offset": start,
                     "source_bytes": len(source), "source_sha256": hashlib.sha256(source).hexdigest(),
                     "width": 8, "height": 8}]
        anchor = (start, len(source), metadata[0]["source_sha256"])
        if mismatch_anchor:
            anchor = (start, len(source), "0" * 64)
        fake_c275 = types.ModuleType("c275_private_draw_material_chain")
        fake_c275.MEMBER = re.compile(r"decoded_c5/(p\d{3})\.c5\Z")
        fake_c275.ROSTER = {"p000"}
        fake_c275.MAX_ENTRIES = 2048
        fake_c275.MAX_MODEL = 64 * 1024 * 1024
        fake_c275.MAX_TOTAL = 1024 * 1024 * 1024
        fake_c276 = types.ModuleType("c276_private_source_texture_coverage")
        fake_c276.read_catalog = lambda path: {"p000": {0: anchor}}
        fake_c279 = types.ModuleType("c279_private_header_texture_base")
        fake_c279.source_descriptor_metadata = lambda raw: metadata
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for part in (1, 2, 3):
                with zipfile.ZipFile(root / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as z:
                    if part == 1:
                        z.writestr("decoded_c5/p000.c5", source_bytes)
            if corrupt:
                p3px = p3px[:-1] + bytes((p3px[-1] ^ 1,))
            with zipfile.ZipFile(root / "textures.zip", "w") as z:
                z.writestr("textures/p000/t000.p3px", p3px)
            with patch.dict(sys.modules, {"c275_private_draw_material_chain": fake_c275,
                                          "c276_private_source_texture_coverage": fake_c276,
                                          "c279_private_header_texture_base": fake_c279}):
                return audit(root, root / "fake.csv", root / "textures.zip", require_full=True)

    def test_private_audit_synthetic_unique_candidate(self):
        result = self.run_audit()
        self.assertEqual(result["summary"]["counts"]["unique_candidate_agrees_with_C78"], 1)
        self.assertEqual(result["summary"]["counts"]["candidate_agreement_pixels"], 64)
        self.assertFalse(result["summary"]["independent_gpu_format_verified"])

    def test_private_audit_corruption_not_claimed(self):
        result = self.run_audit(corrupt=True)
        self.assertEqual(result["summary"]["counts"]["no_supported_candidate_not_verified"], 1)

    def test_private_audit_bad_sha_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, "source SHA mismatch"):
            self.run_audit(mismatch_anchor=True)


if __name__ == "__main__":
    unittest.main()
