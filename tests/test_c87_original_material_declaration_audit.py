"""C87 original shader/declaration parser tests use synthetic bytes only."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import csv
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c87_original_material_declaration_audit import (
    shader_declarations,channel_hint,collect
)
def fixture(strings):
    buf=bytearray(128)
    buf[:2]=b"\xc5x"
    struct.pack_into("<I",buf,0x64,128)
    for text in strings:buf+=text.encode("ascii")+b"\0"
    end=len(buf)
    buf+=bytes(64)
    return bytes(buf),end
class OriginalShaderTests(unittest.TestCase):
    def test_extract_verified_source_declaration_flags(self):
        raw,end=fixture(["kawa;;;CF_TEXTURE,CF_COLORMAP,CF_BUMPMAP",
                         "shadow;;;CF_WEIGHT,CF_CASTSHADOW"])
        got=shader_declarations(raw,end)
        self.assertEqual(len(got),2)
        self.assertEqual(got[0][0],"kawa")
        self.assertEqual(got[0][2],["CF_TEXTURE","CF_COLORMAP","CF_BUMPMAP"])
        self.assertEqual(got[1][0],"shadow")
    def test_invalid_source_bytes_and_pointer_fail(self):
        raw,end=fixture(["kawa;;;CF_COLORMAP"])
        with self.assertRaisesRegex(ValueError,"header"):
            shader_declarations(b"WRONG"+raw[5:],end)
        broken=bytearray(raw)
        struct.pack_into("<I",broken,0x64,len(raw)+4)
        with self.assertRaisesRegex(ValueError,"outside"):
            shader_declarations(bytes(broken),end)
    def test_reject_duplicate_capability(self):
        raw,end=fixture(["kawa;;;CF_BUMPMAP,CF_BUMPMAP"])
        with self.assertRaisesRegex(ValueError,"duplicate"):
            shader_declarations(raw,end)
    def test_source_raw_texture_region_is_not_scanned(self):
        raw,end=fixture(["shadow;;;CF_CASTSHADOW"])
        trailing=raw+b"kawa;;;CF_TEXTURE\0"
        self.assertEqual(len(shader_declarations(trailing,end)),1)
    def test_channel_hints_are_nonbinding(self):
        self.assertEqual(channel_hint("Bulba_bodyCl_ctr"),"color_candidate")
        self.assertEqual(channel_hint("Bulba_bodyNorOS_ctr"),"normal_candidate")
        self.assertEqual(channel_hint("BodySp_ctr"),"specular_candidate")
        self.assertEqual(channel_hint("BodyEnv_ctr"),"environment_candidate")
        self.assertEqual(channel_hint("EfFire_fire00_ctr"),"effect_candidate")
        self.assertEqual(channel_hint("unknown_texture"),"unknown_channel")
    def test_collect_rejects_missing_original_model_count(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)
            raw,end=fixture(["kawa;;;CF_COLORMAP"])
            for i in (1,2,3):
                with zipfile.ZipFile(path/f"Pokedex3D_C56_Decoded_C5_Part_{i}_of_3.zip","w") as z:
                    if i==1:z.writestr("decoded_c5/p000.c5",raw)
            csvfile=path/"names.csv"
            with csvfile.open("w",newline="") as fp:
                w=csv.DictWriter(fp,fieldnames=["model_id","index","original_raw_source_offset",
                    "original_name_absolute_offset","original_texture_name"])
                w.writeheader()
            report,models=collect(path,csvfile)
            self.assertEqual(report["source_model_count"],1)
            self.assertTrue(report["errors"])
            self.assertEqual(models[0]["verified_mesh_material_bindings"],0)
if __name__=="__main__":unittest.main()
