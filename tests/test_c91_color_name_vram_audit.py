"""Asset-free C91 original color-name evidence, CRC, and VRAM regressions."""
import pathlib,struct,sys,tempfile,unittest,zlib,zipfile,csv
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c91_color_name_vram_audit import source_color_hint,parse_p3mr,budget,audit

class TestC91SourceColor(unittest.TestCase):
    def test_shader_and_texture_names_must_agree(self):
        row={"source_shader_declaration":"kawa;;;CF_COLORMAP,CF_BUMPMAP",
             "texture_ref0":"0","texture_name0":"bodyCl_ctr",
             "texture_ref1":"1","texture_name1":"bodyNorOS_ctr"}
        self.assertEqual(source_color_hint(row),(0,"bodyCl_ctr"))
        row["source_shader_declaration"]="kawa;;;CF_BUMPMAP"
        self.assertIsNone(source_color_hint(row))
        row["source_shader_declaration"]="kawa;;;CF_COLORMAP"
        row["texture_name0"]="bodyNorOS_ctr"
        self.assertIsNone(source_color_hint(row))
    def test_power_of_two_and_budget_limits(self):
        plan=budget({0:(256,256),1:(256,128),2:(256,128)})
        self.assertLessEqual(plan["planned_bytes"],131072)
        self.assertGreater(plan["resizes"],0)
        with self.assertRaisesRegex(ValueError,"capacity"):
            budget({i:(8,8) for i in range(9)})
        with self.assertRaisesRegex(ValueError,"power-of-two"):
            budget({0:(7,8)})
    def test_source_sidecar_rejects_corruption(self):
        body=struct.pack("<6H",0,2,1,0,1,0x0c02)
        good=struct.pack("<4sHHHHI",b"P3MR",1,25,2,1,zlib.crc32(body))+body
        self.assertEqual(parse_p3mr(good,25),[(1,0,1,2)])
        with self.assertRaisesRegex(ValueError,"header"):parse_p3mr(good,24)
        with self.assertRaisesRegex(ValueError,"checksum"):parse_p3mr(good[:-1]+b"Z",25)
        bad=struct.pack("<6H",1,2,1,0,1,0x0c02)
        malformed=struct.pack("<4sHHHHI",b"P3MR",1,25,2,1,zlib.crc32(bad))+bad
        with self.assertRaisesRegex(ValueError,"range"):parse_p3mr(malformed,25)
    def test_small_synthetic_private_archive_cannot_claim_full_batch(self):
        with tempfile.TemporaryDirectory() as path:
            root=pathlib.Path(path)
            materials=root/"materials.csv";textures=root/"textures.csv";sidecars=root/"sidecars.zip"
            with materials.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["model_id","material_index","source_shader_declaration",
                    "texture_ref0","texture_name0","texture_ref1","texture_name1"])
                w.writeheader()
                w.writerow({"model_id":"p025","material_index":"1",
                    "source_shader_declaration":"kawa;;;CF_COLORMAP",
                    "texture_ref0":"0","texture_name0":"bodyCl_ctr",
                    "texture_ref1":"1","texture_name1":"bodyNorOS_ctr"})
            with textures.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["model_id","index","original_name","ds_width","ds_height"])
                w.writeheader()
                w.writerow({"model_id":"p025","index":"0","original_name":"bodyCl_ctr",
                    "ds_width":"256","ds_height":"128"})
            body=struct.pack("<6H",0,1,1,0,1,0x0c02)
            sidecar=struct.pack("<4sHHHHI",b"P3MR",1,25,1,1,zlib.crc32(body))+body
            with zipfile.ZipFile(sidecars,"w") as z:
                z.writestr("source_material_candidates/p025.p3mr",sidecar)
            with self.assertRaisesRegex(ValueError,"538"):
                audit(materials,textures,sidecars)
if __name__=="__main__":unittest.main()
