"""Synthetic C89 descriptor/geometry regression tests (no copyrighted assets)."""
import pathlib,struct,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c89_mesh_descriptor_join_audit import descriptor_pairs,obj_groups,audit

def c5():
    b=bytearray(0x180);b[:2]=b"\xc5x"
    struct.pack_into("<2H",b,0x14,2,2)
    struct.pack_into("<3I",b,0x3c,0x78,0xa0,0xb8)
    for i,(v,f) in enumerate(((3,2),(4,1))):
        struct.pack_into("<5I",b,0x78+i*20,0xc0+i*40,0,(12<<16)|v,0x264420,0)
        struct.pack_into("<3I",b,0xa0+i*12,0x120+i*12,0,(2<<16)|f*3)
    return bytes(b)
def obj(truncated=False):
    lines=["o p000_mesh_0"]+["v 0 0 0"]*3+["f 1 2 3","f 3 2 1"]
    if not truncated:lines+=["o p000_mesh_1"]+["v 0 0 1"]*4+["f 4 5 6"]
    return ("\n".join(lines)+"\n").encode()
def fixture(path,truncated=False):
    root=pathlib.Path(path)
    with zipfile.ZipFile(root/"Pokedex3D_C7_Validated_Geometry_OBJ_Collection.zip","w") as z:
        z.writestr("models/p000.obj",obj(truncated))
    for part in (1,2,3):
        with zipfile.ZipFile(root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip","w") as z:
            if part==1:z.writestr("decoded_c5/p000.c5",c5())
    return root
class C89Tests(unittest.TestCase):
    def test_counts_and_width(self):
        d=descriptor_pairs(c5())
        self.assertEqual([x["vertices"] for x in d],[3,4])
        self.assertEqual([x["faces"] for x in d],[2,1])
        self.assertEqual([x["index_width"] for x in d],[2,2])
    def test_reject_vertex_pointer(self):
        b=bytearray(c5());struct.pack_into("<I",b,0x78,0x10000)
        with self.assertRaisesRegex(ValueError,"vertex descriptor"):descriptor_pairs(bytes(b))
    def test_reject_index_width(self):
        b=bytearray(c5());struct.pack_into("<I",b,0xa0+8,(1<<16)|6)
        with self.assertRaisesRegex(ValueError,"index descriptor"):descriptor_pairs(bytes(b))
    def test_obj_order(self):
        groups,total,global_vertices=obj_groups(obj())
        self.assertEqual([x["faces"] for x in groups],[2,1])
        self.assertEqual((total,global_vertices),(7,0))
    def test_malformed_obj_rejected(self):
        with self.assertRaisesRegex(ValueError,"nontriangle"):
            obj_groups(b"o mesh\nv 0 0 0\nf 1 2 3 4\n")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            obj_groups(b"o mesh\nv 0 0 0\nf 1 2 3\no mesh\nv 0 0 0\nf 1 2 3\n")
    def test_matched_counts_do_not_imply_material(self):
        with tempfile.TemporaryDirectory() as d:
            meshes,models,report=audit(fixture(d))
            self.assertEqual(report["descriptors_with_matching_export_counts"],2)
            self.assertEqual(report["verified_mesh_material_links"],0)
            self.assertTrue(all(not x["original_material_id"] for x in meshes))
            self.assertEqual(models[0]["status"],"COUNTS_AND_ORDER_MATCH")
            self.assertTrue(report["errors"]) # only synthetic p000, not all 730
    def test_missing_group_is_queued(self):
        with tempfile.TemporaryDirectory() as d:
            meshes,models,report=audit(fixture(d,True))
            self.assertEqual(report["descriptors_with_matching_export_counts"],1)
            self.assertEqual(report["descriptors_incomplete"],1)
            self.assertEqual(report["incomplete_model_ids"],["p000"])
            self.assertEqual(meshes[-1]["source_mesh_status"],"MISSING_ORIGINAL_OBJ_GROUP")
            self.assertEqual(meshes[-1]["mesh_material_status"],"UNVERIFIED")
if __name__=="__main__":unittest.main()
