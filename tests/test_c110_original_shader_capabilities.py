"""C110 original-source shader declaration recovery: synthetic C5 only."""
import csv
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c110_original_shader_capabilities import build,sidecar
from test_c88_original_material_references import sample

def fixture(root,raw=None,tex=None):
    if raw is None: raw,tex=sample()
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip","w") as z:
            if part==1:z.writestr("decoded_c5/p000.c5",raw)
    path=root/"texture_names.csv"
    with path.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["model_id",*tex[0].keys()])
        writer.writeheader()
        for row in tex:
            writer.writerow({"model_id":"p000",**row})
    return path

class ShaderCapsTests(unittest.TestCase):
    def test_source_shader_flags_are_source_declarations_not_sampler_roles(self):
        raw,tex=sample()
        encoded,counts=sidecar("p000",raw,tex)
        self.assertEqual(counts["original_sampler_roles_verified"],0)
        self.assertEqual(counts["declared_colormap_materials"],1)
        self.assertEqual(counts["ambiguous_two_texture_colormap_materials"],1)
        self.assertEqual(len(encoded),16+2*10)
        self.assertEqual(struct.unpack_from("<4s4HI",encoded,0)[:5],
                         (b"P3SC",1,0,2,0))
        self.assertEqual(struct.unpack_from("<5H",encoded,16),
                         (0,0,0,1,1))
        self.assertEqual(struct.unpack_from("<5H",encoded,26),
                         (1,1,65535,65535,0))

    def test_private_p3sc_zip_contains_no_original_c5_or_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            csvpath=fixture(root)
            out=root/"shader_caps.zip"
            result=build(root,csvpath,out)
            self.assertEqual(result["models"],1)
            self.assertTrue(result["requires_private_shader_sampler_decode"])
            with zipfile.ZipFile(out) as z:
                self.assertEqual(z.namelist(),["materials/p000.p3sc"])
                self.assertTrue(z.read("materials/p000.p3sc").startswith(b"P3SC"))
            with self.assertRaisesRegex(ValueError,"730"):
                build(root,csvpath,root/"bad.zip",require_full=True)
            self.assertFalse((root/"bad.zip").exists())

    def test_source_shader_bumpmap_does_not_claim_color(self):
        raw,tex=sample()
        raw=raw.replace(b"CF_COLORMAP",b"CF_BUMPMAP")
        encoded,counts=sidecar("p000",raw,tex)
        self.assertEqual(counts["declared_colormap_materials"],0)
        self.assertEqual(counts["original_sampler_roles_verified"],0)
        self.assertEqual(struct.unpack_from("<5H",encoded,16)[-1],2)

    def test_missing_cross_checked_C75_cannot_emit_role_provenance(self):
        raw,tex=sample()
        with self.assertRaisesRegex(ValueError,"mandatory"):
            sidecar("p000",raw,[])
        tex[0]["original_name_absolute_offset"]="471"
        with self.assertRaisesRegex(ValueError,"pointer"):
            sidecar("p000",raw,tex)

    def test_corrupt_original_shader_reference_fails(self):
        raw,tex=sample()
        raw=bytearray(raw)
        struct.pack_into("<I",raw,192,0xffff0009)
        with self.assertRaisesRegex(ValueError,"shader reference"):
            sidecar("p000",bytes(raw),tex)

if __name__=="__main__":
    unittest.main()
