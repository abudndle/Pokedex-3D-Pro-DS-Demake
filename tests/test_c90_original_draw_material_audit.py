"""C90 synthetic original material-selector and C-sidecar loader tests."""
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c90_original_draw_material_audit import draws,primary_map
ROOT=pathlib.Path(__file__).resolve().parents[1]

def sample():
    b=bytearray(0x400);b[:2]=b"\xc5x"
    struct.pack_into("<H",b,0x10,4)
    struct.pack_into("<2H",b,0x14,2,2)
    struct.pack_into("<H",b,0x18,4)
    struct.pack_into("<3I",b,0x3c,120,160,184)
    struct.pack_into("<I",b,0x50,344)
    struct.pack_into("<3I",b,160,512,0,(2<<16)|6)
    struct.pack_into("<3I",b,172,560,0,(2<<16)|3)
    for i,(material,mesh,mode,faces) in enumerate((
            (1,0,0x0c02,2),(0,1,0x0c02,1),
            (3,0,0x0c01,2),(3,1,0x0c01,1))):
        struct.pack_into("<8H6f",b,184+i*40,material,mesh,mesh,31,faces,
                         i,i,mode,*([0.0]*6))
    return bytes(b)

class C90OriginalMaterialTest(unittest.TestCase):
    def test_material_and_mesh_indices(self):
        source,nmesh=draws(sample(),"p000")
        self.assertEqual(len(source),4)
        self.assertEqual((source[0]["material_index"],source[0]["mesh_index"]),(1,0))
        self.assertEqual(primary_map(source,nmesh),({0:1,1:0},[]))
        self.assertTrue(all(x["color_texture_slot"]=="UNVERIFIED" for x in source))
    def test_out_of_bounds_material_fails(self):
        data=bytearray(sample())
        struct.pack_into("<H",data,184,8)
        with self.assertRaisesRegex(ValueError,"mesh/material"):draws(bytes(data),"p000")
    def test_triangle_count_mismatch_fails(self):
        data=bytearray(sample())
        struct.pack_into("<H",data,184+8,3)
        with self.assertRaisesRegex(ValueError,"face count"):draws(bytes(data),"p000")
    def test_repeated_conflicting_primary_draw_unresolved(self):
        source,nmesh=draws(sample(),"p000")
        source.append({**source[0],"material_index":2})
        self.assertEqual(primary_map(source,nmesh),({1:0},[0]))
    def test_reader_accepts_provenance_but_rejects_corruption(self):
        cc=shutil.which("cc")
        if not cc:self.skipTest("C compiler unavailable")
        ranges=struct.pack("<6H",0,2,1,2,3,0x0c02)+struct.pack(
            "<6H",2,1,0,6,7,0x0c02)
        source=struct.pack("<4sHHHHI",b"P3MR",1,25,3,2,zlib.crc32(ranges))+ranges
        with tempfile.TemporaryDirectory() as d:
            folder=pathlib.Path(d)
            good=folder/"good.p3mr";good.write_bytes(source)
            bad=folder/"bad.p3mr";bad.write_bytes(source[:-1]+bytes([source[-1]^1]))
            driver=folder/"driver.c"
            driver.write_text("""
#include "source_material_map.h"
#include <assert.h>
int main(int argc,char **argv){
    P3DSourceMaterialMap m;
    assert(argc==3);
    assert(p3dSourceMaterialLoad(&m,argv[1],25,3));
    assert(m.ready && m.count==2 && m.ranges[0].material_index==1);
    assert(!p3dSourceMaterialLoad(&m,argv[1],26,3));
    assert(!m.ready);
    assert(!p3dSourceMaterialLoad(&m,argv[2],25,3));
    assert(!m.ready);
    return 0;
}
""")
            app=folder/"check"
            subprocess.run([cc,"-std=c11","-O2","-Wall","-Wextra","-Werror",
                            "-I"+str(ROOT/"source"),str(ROOT/"source"/"source_material_map.c"),
                            str(driver),"-o",str(app)],check=True)
            subprocess.run([str(app),str(good),str(bad)],check=True)
if __name__=="__main__":unittest.main()
