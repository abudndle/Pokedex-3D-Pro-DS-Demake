"""C275 synthetic-only C5 draw/material/C75 provenance and isolation tests."""
import csv
import os
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from c275_private_draw_material_chain import join, audit, write_private_report, c75_from_source
from test_c88_original_material_references import sample


def fixture(material=0, mode=0x0c02, faces=1):
    original, tex = sample()
    b = bytearray(original + bytes(200))
    # Real C5 stores source texture-name offsets at +8 in each 28-byte row.
    struct.pack_into("<I", b, 136 + 8, 70)
    struct.pack_into("<I", b, 136 + 28 + 8, 77)
    # Original material/shader/name tables remain unchanged. Add an
    # independently indexed draw/mesh table at the end of this synthetic C5.
    struct.pack_into("<2H", b, 0x14, 1, 1)
    struct.pack_into("<H", b, 0x18, 1)
    struct.pack_into("<3I", b, 0x3c, 520, 540, 552)
    struct.pack_into("<I", b, 0x50, 592)
    struct.pack_into("<3I", b, 540, 620, 0, (2 << 16) | (faces * 3))
    struct.pack_into("<8H", b, 552, material, 0, 0, 0, faces, 0, 0, mode)
    return bytes(b), tex


def archives(folder, raw, tex):
    for part in (1, 2, 3):
        with zipfile.ZipFile(folder / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as z:
            if part == 1:
                z.writestr("decoded_c5/p200.c5", raw)
    csvpath = folder / "c75.csv"
    with csvpath.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["model_id", *tex[0].keys()])
        writer.writeheader()
        for row in tex:
            writer.writerow({"model_id": "p200", **row})
    return csvpath


class C275Tests(unittest.TestCase):
    def test_original_draw_to_material_to_shader_to_c75_refs(self):
        raw, tex = fixture()
        evidence = join("p200", raw, tex)
        row = evidence["draws"][0]
        self.assertEqual((row["mesh_index"], row["material_index"]), (0, 0))
        self.assertEqual(row["source_texture_reference_indices"], [0, 1])
        self.assertEqual(row["source_texture_reference_names"], ["bodyCl", "bodyNorOS"])
        self.assertEqual(row["shader_index"], 0)
        self.assertEqual(evidence["unique_primary_mesh_materials"], 1)
        self.assertFalse(row["gpu_sampler_roles_verified"])
        self.assertFalse(row["p3px_image_binding_verified"])
        self.assertFalse(evidence["release_ready"])

    def test_secondary_draw_does_not_claim_primary(self):
        raw, tex = fixture(material=1, mode=0x0c01)
        evidence = join("p200", raw, tex)
        self.assertEqual(evidence["unresolved_primary_mesh_indices"], [0])
        self.assertEqual(evidence["draws"][0]["source_texture_reference_indices"], [65535, 65535])

    def test_bad_draw_material_reference_rejected(self):
        raw, tex = fixture(material=3)
        with self.assertRaisesRegex(ValueError, "mesh/material"):
            join("p200", raw, tex)

    def test_bad_face_count_rejected(self):
        raw, tex = fixture()
        b = bytearray(raw)
        struct.pack_into("<H", b, 552 + 8, 2)
        with self.assertRaisesRegex(ValueError, "face count"):
            join("p200", bytes(b), tex)

    def test_bad_c75_pointer_and_missing_references_rejected(self):
        raw, tex = fixture()
        tex[0]["original_name_absolute_offset"] = "471"
        with self.assertRaisesRegex(ValueError, "pointer"):
            join("p200", raw, tex)
        with self.assertRaisesRegex(ValueError, "C75 inventory disagrees"):
            join("p200", raw, [])

    def test_invalid_roster_and_bad_material_shader_rejected(self):
        raw, tex = fixture()
        for model in ("p721", "p734", "../p200"):
            with self.subTest(model=model), self.assertRaisesRegex(ValueError, "roster"):
                join(model, raw, tex)
        b = bytearray(raw)
        struct.pack_into("<I", b, 192, 0xffff0008)
        with self.assertRaisesRegex(ValueError, "shader reference"):
            join("p200", bytes(b), tex)

    def test_c75_is_derived_directly_from_original_source_table(self):
        raw, tex = fixture()
        self.assertEqual(c75_from_source(raw), tex)
        self.assertEqual(join("p200", raw)["source_texture_count"], 2)
        damaged = bytearray(raw)
        struct.pack_into("<I", damaged, 136 + 8, 0x7fffffff)
        with self.assertRaisesRegex(ValueError, "pointer outside"):
            join("p200", bytes(damaged))

    def test_private_batch_and_full_roster_gate(self):
        raw, tex = fixture()
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            c75 = archives(folder, raw, tex)
            result = audit(folder, c75)
            self.assertEqual(audit(folder)["summary"]["source_draw_material_links"], 1)
            self.assertEqual(result["summary"]["original_models_checked"], 1)
            self.assertEqual(result["summary"]["source_draw_material_links"], 1)
            self.assertEqual(result["summary"]["source_draw_texture_reference_slots"], 2)
            self.assertEqual(result["summary"]["verified_gpu_sampler_roles"], 0)
            with self.assertRaisesRegex(ValueError, "730"):
                audit(folder, c75, require_full=True)
            report = folder / "private.json"
            write_private_report(report, result)
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
            self.assertIn('"model_id": "p200"', report.read_text())

    def test_duplicate_source_model_rejected(self):
        raw, tex = fixture()
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            c75 = archives(folder, raw, tex)
            with zipfile.ZipFile(folder / "Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip", "a") as z:
                z.writestr("decoded_c5/p200.c5", raw)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                audit(folder, c75)

    def test_duplicate_c75_index_rejected(self):
        raw, tex = fixture()
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            c75 = archives(folder, raw, tex)
            with c75.open("a") as stream:
                stream.write("p200,0,bodyCl,470\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                audit(folder, c75)

    def test_unsafe_output_symlink_and_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            target = folder / "target"
            target.write_text("untouched")
            link = folder / "link"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "unsafe"):
                write_private_report(link, {})
            hardlink = folder / "hardlink"
            os.link(target, hardlink)
            with self.assertRaisesRegex(ValueError, "unsafe"):
                write_private_report(hardlink, {})
            self.assertEqual(target.read_text(), "untouched")


if __name__ == "__main__":
    unittest.main()
