"""C96 bounded P3CS stream regression against native C reader (synthetic only)."""
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
DRIVER=r'''
#include "preview_chunk_stream.h"
#include <assert.h>
#include <stdint.h>
int main(int argc,char **argv){
    static P3DChunkStream s;
    static int16_t xyz[600*9],uv[600*6];
    static unsigned char rgb[600*3];
    assert(argc==5);
    assert(p3dChunkOpen(&s,argv[1],25));
    assert(s.chunk_count==3 && s.total_triangles==1202 && s.original_triangles==5000);
    for(int i=0;i<3;i++){
        assert(p3dChunkRead(&s,(unsigned)i,xyz,uv,rgb));
        assert(rgb[0]==192 && rgb[1]==224 && rgb[2]==232);
    }
    assert(!p3dChunkRead(&s,3,xyz,uv,rgb));
    p3dChunkClose(&s);
    assert(!s.ready);
    assert(!p3dChunkOpen(&s,argv[1],24));
    assert(!p3dChunkOpen(&s,argv[2],25));
    assert(!p3dChunkOpen(&s,argv[3],25));
    assert(!p3dChunkOpen(&s,argv[4],25));
    return 0;
}
'''
def source(chunks=(600,600,2),mutate_index=False):
    records=[]
    for i,n in enumerate(chunks):
        rec=struct.pack("<9h6h3B",*([i]*9),*([200+i]*6),192,224,232)
        records.append(rec*n)
    table=bytearray()
    offset=24+16*len(chunks)
    first=0
    for n,block in zip(chunks,records):
        table+=struct.pack("<IHHII",first,n,0,offset,zlib.crc32(block))
        offset+=len(block)
        first+=n
    if mutate_index:table[0]^=1
    header=struct.pack("<4s4H3I",b"P3CS",1,25,len(chunks),0,first,5000,zlib.crc32(table))
    return header+table+b"".join(records)

class C96ChunkStreamTests(unittest.TestCase):
    def test_native_stream_three_chunks_and_fail_closed(self):
        cc=shutil.which("cc")
        if not cc:self.skipTest("host C compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            good=source()
            values=[
                good,
                good[:-1],                 # truncated terminal chunk
                good[:-1]+bytes([good[-1]^1]), # changed contents with old CRC
                source(mutate_index=True)  # nonzero first triangle
            ]
            paths=[]
            for i,data in enumerate(values):
                path=root/("chunk_%d.p3cs"%i)
                path.write_bytes(data)
                paths.append(str(path))
            (root/"driver.c").write_text(DRIVER)
            exe=root/"native"
            subprocess.run([cc,"-std=c11","-Wall","-Wextra","-Werror",
                "-I"+str(ROOT/"source"),
                str(ROOT/"source"/"preview_chunk_stream.c"),
                str(root/"driver.c"),"-o",str(exe)],check=True)
            subprocess.run([str(exe),*paths],check=True)
    def test_three_chunk_file_contains_no_invented_material_map(self):
        blob=source()
        self.assertEqual(blob[:4],b"P3CS")
        self.assertEqual(struct.unpack_from("<H",blob,8)[0],3)
        self.assertEqual(struct.unpack_from("<I",blob,12)[0],1202)
        self.assertEqual(len(blob),24+48+1202*33)
    def test_one_chunk_supported_and_bounded(self):
        self.assertEqual(struct.unpack_from("<H",source((7,)),8)[0],1)
        self.assertEqual(len(source((600,))),24+16+600*33)
    def test_original_source_face_count_preserved_in_header(self):
        self.assertEqual(struct.unpack_from("<I",source(),16)[0],5000)

if __name__=="__main__":unittest.main()
