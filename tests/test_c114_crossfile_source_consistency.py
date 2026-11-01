"""C114 cross-file original C5 provenance regression: synthetic assets only."""
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_private_release_assets import Assets,audit

def frame(magic,version,model,count,reserved,body):
    return struct.pack("<4s4HI",magic,version,model,count,reserved,
                       zlib.crc32(body))+body

def create(root, *, wrong_shader=False, wrong_texture=False,
           wrong_range=False, wrong_count=False):
    folder=root/"materials"
    folder.mkdir(parents=True,exist_ok=True)
    raw_words=[
        (0,0xffff0002,*([0]*11)),
        (1,0xffff0007,*([0]*11))
    ]
    if wrong_shader:
        raw_words[0]=(9,0xffff0002,*([0]*11))
    if wrong_texture:
        raw_words[0]=(0,0xffff0008,*([0]*11))
    word_body=b"".join(struct.pack("<13I",*words) for words in raw_words)
    (folder/"p000.p3sw").write_bytes(
        frame(b"P3SW",1,0,2,0,word_body))
    shaders=[(0,0,2,65535,1),(1,1,7,65535,1)]
    if wrong_count:
        shaders=shaders[:1]
    shader_body=b"".join(struct.pack("<5H",*row) for row in shaders)
    (folder/"p000.p3sc").write_bytes(
        frame(b"P3SC",2,0,len(shaders),0,shader_body))
    regions=[(0,2,0,2,65535,0x0c02),
             (2,1,1,7,65535,0x0c02)]
    if wrong_range:
        regions[-1]=(2,1,1,8,65535,0x0c02)
    region_body=b"".join(struct.pack("<6H",*row) for row in regions)
    (folder/"p000.p3mr").write_bytes(
        frame(b"P3MR",1,0,3,2,region_body))

def run_audit(root):
    source=Assets(root)
    try:return audit(source)
    finally:source.close()

class C114SourceJoinTests(unittest.TestCase):
    def test_three_crc_valid_original_sidecars_join(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            create(root)
            result=run_audit(root)
            self.assertFalse(any("p000.p3sw" in x for x in result["invalid"]))
            self.assertFalse(any("p000.p3sc" in x for x in result["invalid"]))
            self.assertFalse(any("p000.p3mr" in x for x in result["invalid"]))
            self.assertFalse(any("P3SW/P3SC/P3MR references disagree" in x
                                 for x in result["invalid"]))
            # Complete original-game validation remains blocked: only one
            # synthetic C5 model is present and no real Nintendo art exists.
            self.assertFalse(result["asset_complete"])
            self.assertFalse(result["original_shader_sampler_roles_verified"])

    def test_crc_valid_but_inconsistent_original_source_is_rejected(self):
        for changed in ("wrong_shader","wrong_texture","wrong_range","wrong_count"):
            with self.subTest(change=changed):
                with tempfile.TemporaryDirectory() as folder:
                    root=pathlib.Path(folder)
                    create(root,**{changed:True})
                    result=run_audit(root)
                    self.assertTrue(any(
                        "materials/p000: original C5 P3SW/P3SC/P3MR references disagree"
                        in message for message in result["invalid"]),
                        result["invalid"])

    def test_missing_file_stays_missing_without_duplicate_crossfile_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            create(root)
            (root/"materials/p000.p3sc").unlink()
            result=run_audit(root)
            self.assertFalse(any("P3SW/P3SC/P3MR references disagree" in x
                                 for x in result["invalid"]))
            self.assertEqual(result["counts"]["source_C5_shader_capabilities"],0)

if __name__=="__main__":
    unittest.main()
