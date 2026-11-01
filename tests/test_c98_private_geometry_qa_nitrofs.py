"""C98 private compare-pack integration tests with synthetic models only."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c98_build_private_geometry_qa_nitrofs import (
    build, qa_species_map, validate_p3cs, inspect_sources
)
TEST_IDS=(0,1,25)

def make_chunk(model):
    tri=struct.pack("<9h6h3B",*([model]*9),*([0]*6),192,224,232)
    table=struct.pack("<IHHII",0,1,0,40,zlib.crc32(tri))
    return struct.pack("<4s4H3I",b"P3CS",1,model,1,0,1,100,zlib.crc32(table))+table+tri

def write_pair(root, corrupt=False, add_existing_map=False):
    original=root/"legacy.zip";chunks=root/"chunk.zip"
    with zipfile.ZipFile(original,"w") as z:
        for model in TEST_IDS:
            z.writestr("preview/p%03d.ds3m"%model,
                       struct.pack("<4sHHII9h",b"DS3M",1,1,3,100,*([0]*9)))
        if add_existing_map:z.writestr("models/species_map.p3sm",b"TEST")
    with zipfile.ZipFile(chunks,"w") as z:
        for model in TEST_IDS:
            content=make_chunk(model)
            if model==25 and corrupt:content=content[:-1]+bytes([content[-1]^1])
            z.writestr("diagnostic_nitrofs/preview/p%03d.p3cs"%model,content)
    return original,chunks

class TestC98(unittest.TestCase):
    def test_private_qa_bundle_preserves_both_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b=write_pair(root)
            result=build(a,b,root/"result.zip",3,3)
            self.assertEqual(result["entries"],7)
            self.assertEqual(result["chunk_model_count"],3)
            self.assertFalse(result["release_ready"])
            with zipfile.ZipFile(root/"result.zip") as z:
                self.assertEqual(len(z.namelist()),7)
                self.assertIn("preview/p000.ds3m",z.namelist())
                self.assertIn("preview/p000.p3cs",z.namelist())
                mapdata=z.read("models/species_map.p3sm")
                self.assertEqual(len(mapdata),1306)
                self.assertEqual(struct.unpack_from("<3H",mapdata,8),(0,1,0xffff))
                self.assertEqual(struct.unpack_from("<H",mapdata,8+24*2)[0],25)
    def test_corrupt_original_source_chunk_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b=write_pair(root,corrupt=True)
            with self.assertRaisesRegex(ValueError,"corrupt original-derived"):
                build(a,b,root/"result.zip",3,3)
    def test_existing_mapping_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b=write_pair(root,add_existing_map=True)
            with self.assertRaisesRegex(ValueError,"cannot overwrite"):
                build(a,b,root/"result.zip",3,3)
    def test_reject_wrong_model_identifier(self):
        damaged=bytearray(make_chunk(0))
        struct.pack_into("<H",damaged,6,1)
        with self.assertRaisesRegex(ValueError,"header"):
            validate_p3cs(bytes(damaged),0)
    def test_reject_missing_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            a,b=write_pair(root)
            with self.assertRaisesRegex(ValueError,"incorrect"):
                inspect_sources(a,b,4,3)
if __name__=="__main__":unittest.main()
