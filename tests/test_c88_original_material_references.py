"""C88 original-data material reference regression tests; synthetic fixtures only."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import csv

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c88_original_material_references import parse,scan

def sample():
    data=bytearray(520)
    data[:2]=b"\xc5x"
    struct.pack_into("<3H",data,0x0c,2,2,2)
    struct.pack_into("<4I",data,0x2c,120,136,192,296)
    struct.pack_into("<I",data,0x64,400)
    struct.pack_into("<2I",data,120,0,0)
    struct.pack_into("<2I",data,128,0,24)
    data[400:424]=b"kawa;;;CF_COLORMAP\0".ljust(24,b"\0")
    data[424:452]=b"shadow;;;CF_CASTSHADOW\0".ljust(28,b"\0")
    data[452:458]=b"BodyA\0"
    data[460:467]=b"shadow\0"
    struct.pack_into("<13I",data,192,0xffff0000,0x00010000,0,0,0,0,0,0,52,0,0,0,0)
    struct.pack_into("<13I",data,244,0xffff0001,0xffffffff,0,0,0,0,0,0,60,0,0,0,0)
    data[470:477]=b"bodyCl\0"
    data[477:487]=b"bodyNorOS\0"
    textures=[
        {"index":"0","original_texture_name":"bodyCl","original_name_absolute_offset":"470"},
        {"index":"1","original_texture_name":"bodyNorOS","original_name_absolute_offset":"477"}]
    return bytes(data),textures

class MaterialSourceTests(unittest.TestCase):
    def test_original_shader_and_texture_links(self):
        data,tex=sample()
        records,meta=parse(data,tex)
        self.assertEqual(meta["nmaterial"],2)
        self.assertEqual(records[0][1],"BodyA")
        self.assertEqual(records[0][2],0)
        self.assertEqual(records[0][4:6],(0,1))
        self.assertEqual(records[0][6:8],("bodyCl","bodyNorOS"))
        self.assertEqual(records[1][1],"shadow")
        self.assertEqual(records[1][4:6],(65535,65535))
        self.assertEqual(records[0][-1],"UNVERIFIED")
    def test_malformed_shader_index_fails(self):
        data,tex=sample()
        data=bytearray(data)
        struct.pack_into("<I",data,192,0xffff0009)
        with self.assertRaisesRegex(ValueError,"shader reference"):
            parse(bytes(data),tex)
    def test_malformed_texture_index_fails(self):
        data,tex=sample()
        data=bytearray(data)
        struct.pack_into("<I",data,196,0x00090000)
        with self.assertRaisesRegex(ValueError,"texture reference"):
            parse(bytes(data),tex)
    def test_corrupted_texture_provenance_fails(self):
        data,tex=sample()
        tex[0]["original_name_absolute_offset"]="471"
        with self.assertRaisesRegex(ValueError,"C75 texture name pointer"):
            parse(data,tex)
    def test_corrupted_material_table_stride_fails(self):
        data,tex=sample()
        data=bytearray(data)
        struct.pack_into("<I",data,0x34,201)
        with self.assertRaisesRegex(ValueError,"stride/count"):
            parse(bytes(data),tex)
    def test_incomplete_source_archive_not_marked_verified(self):
        data,tex=sample()
        records,meta=parse(data,[])
        self.assertEqual(records[0][6],"UNKNOWN_SOURCE_ARCHIVE")
        self.assertEqual(records[0][-2],"C5_ONLY_MISSING_C75")
    def test_full_model_inventory_must_be_present(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            data,tex=sample()
            for part in (1,2,3):
                with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip","w") as z:
                    if part==1:z.writestr("decoded_c5/p000.c5",data)
            path=root/"names.csv"
            with path.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["model_id",*tex[0].keys()])
                w.writeheader()
                for row in tex:w.writerow({"model_id":"p000",**row})
            rows,models,report=scan(root,path)
            self.assertEqual(len(rows),2)
            self.assertEqual(report["material_references"],2)
            self.assertTrue(report["errors"])
            self.assertEqual(report["verified_face_material_ranges"],0)

if __name__=="__main__":unittest.main()
