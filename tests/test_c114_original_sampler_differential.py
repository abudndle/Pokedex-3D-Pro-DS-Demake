"""C114 verified-source differential tests; synthetic C5 materials only."""
import copy
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c114_original_sampler_differential import differential_report,validate_model
from c111_original_sampler_evidence import material_evidence
from test_c88_original_material_references import sample

def source_data():
    c5,texture_names=sample()
    first,_=material_evidence("p000",c5,texture_names)
    second=bytearray(c5)
    # Change one original *unknown* C5 operation word and the known
    # original texture-reference layout; C88 pointer validation still runs.
    struct.pack_into("<I",second,200,0xc0ffee)
    struct.pack_into("<I",second,196,0xffff0000)
    other,_=material_evidence("p001",bytes(second),texture_names)
    return first,other

def package(folder,entries):
    path=pathlib.Path(folder)/"private_source.zip"
    with zipfile.ZipFile(path,"w") as archive:
        for model,data in entries.items():
            archive.writestr(f"evidence/{model}.json",json.dumps(data))
    return path

class C114DifferentialTests(unittest.TestCase):
    def test_source_verified_operation_word_variation_not_sampler_decoder(self):
        a,b=source_data()
        with tempfile.TemporaryDirectory() as folder:
            path=package(folder,{"p000":a,"p001":b})
            result=differential_report(path)
            self.assertEqual(result["source_model_count"],2)
            self.assertEqual(result["original_material_count"],4)
            self.assertEqual(result["original_GPU_sampler_roles_decoded"],0)
            self.assertTrue(result["source_shader_instruction_disassembly_required"])
            self.assertFalse(result["release_ready"])
            self.assertNotIn("shader_declaration",result["groups"][0])
            groups=[x for x in result["groups"] if
                    "two_distinct_slots" in x["source_texture_reference_layouts"]]
            self.assertEqual(len(groups),1)
            self.assertEqual(groups[0]["source_texture_reference_layouts"],
                             {"only_slot_0":1,"two_distinct_slots":1})
            self.assertIn(2,groups[0]["unknown_material_word_offsets_with_variation"])
            self.assertIn(2,groups[0]["unknown_word_offsets_differing_by_reference_layout"])
            self.assertEqual(groups[0]["verified_color_sampler_assignments"],0)

    def test_byte_tampering_rejected_even_with_valid_archive(self):
        a,b=source_data()
        a["evidence"][0]["source_material_words_hex"][2]="0x11111111"
        with tempfile.TemporaryDirectory() as folder:
            path=package(folder,{"p000":a,"p001":b})
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                differential_report(path)

    def test_source_texture_reference_mismatch_rejected(self):
        a,b=source_data()
        a["evidence"][0]["source_texture_references"]=[8,1]
        with tempfile.TemporaryDirectory() as folder:
            path=package(folder,{"p000":a,"p001":b})
            with self.assertRaisesRegex(ValueError,"shader/texture references"):
                differential_report(path)

    def test_no_completeness_or_gpu_role_claim_from_partial_inventory(self):
        a,b=source_data()
        with tempfile.TemporaryDirectory() as folder:
            path=package(folder,{"p000":a,"p001":b})
            with self.assertRaisesRegex(ValueError,"730"):
                differential_report(path,require_full=True)
            self.assertEqual(differential_report(path)["original_GPU_sampler_roles_decoded"],0)
            a["original_GPU_sampler_roles_verified"]=1
            path=package(folder,{"p000":a})
            with self.assertRaisesRegex(ValueError,"metadata"):
                differential_report(path)

if __name__=="__main__":
    unittest.main()
