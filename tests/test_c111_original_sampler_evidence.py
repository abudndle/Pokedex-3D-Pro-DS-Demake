"""Synthetic C111 tests; never ingest Nintendo proprietary bytes in GitHub."""
import csv
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from c111_original_sampler_evidence import material_evidence, collect
from test_c88_original_material_references import sample

def archive_fixture(path, *, corrupted=False):
    raw, textures = sample()
    if corrupted:
        b=bytearray(raw)
        struct.pack_into("<I", b, 196, 0x00090000)
        raw=bytes(b)
    for part in (1,2,3):
        with zipfile.ZipFile(path/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as z:
            if part==1:
                z.writestr("decoded_c5/p000.c5",raw)
    names=path/"original_c75.csv"
    with names.open("w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=["model_id",*textures[0].keys()])
        w.writeheader()
        for t in textures:w.writerow({"model_id":"p000",**t})
    return names

class SourceSamplerEvidenceTests(unittest.TestCase):
    def test_exact_original_material_dwords_no_inferred_sampler_roles(self):
        raw, tex = sample()
        result, status = material_evidence("p000",raw,tex)
        self.assertEqual(result["material_count"],2)
        self.assertEqual(result["original_GPU_sampler_roles_verified"],0)
        self.assertEqual(result["evidence"][0]["source_texture_references"],[0,1])
        self.assertEqual(result["evidence"][0]["source_material_words_hex"][1],"0x00010000")
        self.assertEqual(result["evidence"][0]["source_sampler_role_status"],
                         "MULTIPLE_OR_MISSING_REFERENCES_UNRESOLVED")
        self.assertFalse(result["evidence"][0]["original_color_sampler_slot_verified"])
        self.assertEqual(status["MULTIPLE_OR_MISSING_REFERENCES_UNRESOLVED"],1)
        self.assertEqual(status["NO_COLORMAP_DECLARATION"],1)

    def test_original_single_texture_is_only_a_candidate(self):
        raw, tex=sample()
        b=bytearray(raw)
        struct.pack_into("<I",b,196,0xffff0000)
        result,status=material_evidence("p000",bytes(b),tex)
        self.assertEqual(status["SINGLE_REFERENCE_COLOR_CANDIDATE_NOT_GPU_VERIFIED"],1)
        self.assertEqual(result["original_GPU_sampler_roles_verified"],0)

    def test_original_colormap_and_bumpmap_is_unresolved(self):
        raw, tex=sample()
        b=bytearray(raw)
        # Move the first shader name pointer to a new source string in the
        # synthetic C5 string table without changing the C75 source names.
        b.extend(bytes(200))
        b[540:540+len(b"kawa;;;CF_COLORMAP,CF_BUMPMAP\0")]=b"kawa;;;CF_COLORMAP,CF_BUMPMAP\0"
        struct.pack_into("<I",b,124,140)  # C5 strings base=400, target=540
        struct.pack_into("<I",b,196,0xffff0000)
        result,status=material_evidence("p000",bytes(b),tex)
        self.assertEqual(status["COLORMAP_WITH_BUMPMAP_UNRESOLVED"],1)
        self.assertFalse(result["evidence"][0]["original_normal_sampler_slot_verified"])

    def test_private_archive_produces_only_evidence_and_summary(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)
            names=archive_fixture(p)
            target=p/"private_evidence.zip"
            result=collect(p,names,target)
            self.assertEqual(result["original_models_inspected"],1)
            self.assertEqual(result["verified_GPU_color_sampler_slots"],0)
            self.assertFalse(result["release_ready"])
            with zipfile.ZipFile(target) as z:
                self.assertEqual(sorted(z.namelist()),
                                 ["C111_sampler_evidence_report.json","evidence/p000.json"])
                model=json.loads(z.read("evidence/p000.json"))
                self.assertEqual(model["material_count"],2)
                self.assertEqual(len(model["evidence"][0]["source_material_words_hex"]),13)
            with self.assertRaisesRegex(ValueError,"730"):
                collect(p,names,p/"invalid.zip",require_full=True)
            self.assertFalse((p/"invalid.zip").exists())

    def test_bad_C5_source_and_C75_pointer_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)
            names=archive_fixture(p,corrupted=True)
            with self.assertRaisesRegex(ValueError,"texture reference"):
                collect(p,names,p/"bad.zip")
            self.assertFalse((p/"bad.zip").exists())
        raw,tex=sample()
        tex[0]["original_name_absolute_offset"]="471"
        with self.assertRaisesRegex(ValueError,"pointer"):
            material_evidence("p000",raw,tex)
        with self.assertRaisesRegex(ValueError,"C75"):
            material_evidence("p000",raw,[])

    def test_source_shader_flags_or_indices_corrupt(self):
        raw,tex=sample()
        b=bytearray(raw)
        struct.pack_into("<I",b,192,0xffff000a)
        with self.assertRaisesRegex(ValueError,"shader reference"):
            material_evidence("p000",bytes(b),tex)
        with self.assertRaisesRegex(ValueError,"invalid C5 model ID"):
            material_evidence("../other",raw,tex)

if __name__=="__main__":
    unittest.main()
