"""C113 synthetic original C5 13-word sidecar tests (no Nintendo data)."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from c113_private_material_words import encode_source_words,build
from test_c88_original_material_references import sample
from test_c111_original_sampler_evidence import archive_fixture

class MaterialWordTests(unittest.TestCase):
    def test_preserves_all_original_c5_operation_dwords(self):
        raw,names=sample()
        blob=encode_source_words("p000",raw,names)
        self.assertEqual(struct.unpack_from("<4s4HI",blob,0)[:5],
                         (b"P3SW",1,0,2,0))
        self.assertEqual(len(blob),16+52*2)
        self.assertEqual(zlib.crc32(blob[16:]),
                         struct.unpack_from("<I",blob,12)[0])
        self.assertEqual(struct.unpack_from("<13I",blob,16),
                         struct.unpack_from("<13I",raw,192))
        self.assertEqual(struct.unpack_from("<13I",blob,68),
                         struct.unpack_from("<13I",raw,244))

    def test_original_shader_and_texture_pointer_checks(self):
        raw,names=sample()
        broken=bytearray(raw)
        struct.pack_into("<I",broken,196,0x00090000)
        with self.assertRaisesRegex(ValueError,"texture reference"):
            encode_source_words("p000",bytes(broken),names)
        names[0]["original_name_absolute_offset"]="471"
        with self.assertRaisesRegex(ValueError,"pointer"):
            encode_source_words("p000",raw,names)

    def test_original_c5_invalid_model_id_fails_closed(self):
        raw,names=sample()
        with self.assertRaisesRegex(ValueError,"invalid C5 model ID"):
            encode_source_words("../x",raw,names)

    def test_privately_packaged_sidecar_and_full_roster_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            names=archive_fixture(root)
            result=build(root,names,root/"private.zip")
            self.assertEqual(result["models"],1)
            self.assertEqual(result["original_C5_material_words"],26)
            self.assertEqual(result["verified_original_GPU_sampler_roles"],0)
            with zipfile.ZipFile(root/"private.zip") as z:
                self.assertEqual(z.namelist(),["materials/p000.p3sw"])
                self.assertEqual(z.read("materials/p000.p3sw")[:4],b"P3SW")
            with self.assertRaisesRegex(ValueError,"730"):
                build(root,names,root/"missing.zip",require_full=True)
            self.assertFalse((root/"missing.zip").exists())

if __name__=="__main__":
    unittest.main()
