"""C97: synthetic only — validate batched native P3CS read, CRC and I/O cap."""
import pathlib, shutil, struct, subprocess, tempfile, unittest, zlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/"source"/"preview_chunk_stream.c"
DRIVER=r'''
#include "preview_chunk_stream.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static unsigned calls;
size_t tracked_fread(void *p,size_t s,size_t n,FILE *f){
    calls++;
    return fread(p,s,n,f);
}
int main(int argc,char **argv){
    static P3DChunkStream stream;
    static int16_t xyz[600*9],uv[600*6];
    static unsigned char rgb[600*3];
    assert(argc==4);
    assert(p3dChunkOpen(&stream,argv[1],25));
    assert(stream.chunk_count==3 && stream.total_triangles==1202);
    for(unsigned i=0;i<stream.chunk_count;i++){
        assert(p3dChunkRead(&stream,i,xyz,uv,rgb));
        for(unsigned j=0;j<stream.chunks[i].triangles;j++){
            assert(xyz[j*9]==(int16_t)(i+100));
            assert(uv[j*6]==(int16_t)(i+200));
            assert(rgb[j*3]==192 && rgb[j*3+1]==224 && rgb[j*3+2]==232);
        }
    }
    assert(calls<=100); /* C96 per-triangle reads exceeded 1500 calls */
    p3dChunkClose(&stream);
    assert(!p3dChunkOpen(&stream,argv[2],25)); /* bad CRC */
    assert(!p3dChunkOpen(&stream,argv[3],25)); /* bad index CRC */
    assert(!stream.ready);
    printf("C97 synthetic source stream: %u read calls PASS\n",calls);
    return 0;
}
'''
def make_file(counts=(600,600,2)):
    blocks=[]
    for i,n in enumerate(counts):
        rec=struct.pack("<9h6h3B",*([100+i]*9),*([200+i]*6),192,224,232)
        blocks.append(rec*n)
    table=bytearray()
    off=24+16*len(blocks)
    first=0
    for n,blob in zip(counts,blocks):
        table.extend(struct.pack("<IHHII",first,n,0,off,zlib.crc32(blob)))
        first+=n;off+=len(blob)
    return struct.pack("<4s4H3I",b"P3CS",1,25,len(blocks),0,first,5000,zlib.crc32(table))+table+b"".join(blocks)

class C97Tests(unittest.TestCase):
    def test_chunked_native_crc_and_io_efficiency(self):
        cc=shutil.which("cc")
        if not cc:self.skipTest("C compiler unavailable")
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            original=make_file()
            filenames=[root/str(i) for i in range(3)]
            filenames[0].write_bytes(original)
            bad=bytearray(original);bad[-1]^=1
            filenames[1].write_bytes(bad)
            bad=bytearray(original);bad[24]^=1
            filenames[2].write_bytes(bad)
            (root/"driver.c").write_text(DRIVER)
            subprocess.run([cc,"-std=c11","-O2","-Wall","-Wextra","-Werror",
                "-I"+str(ROOT/"source"),"-Dfread=tracked_fread",
                "-c",str(SOURCE),"-o",str(root/"reader.o")],check=True)
            subprocess.run([cc,"-std=c11","-O2","-Wall","-Wextra","-Werror",
                "-I"+str(ROOT/"source"),str(root/"driver.c"),
                str(root/"reader.o"),"-o",str(root/"test")],check=True)
            out=subprocess.run([str(root/"test"),*(str(f) for f in filenames)],
                               capture_output=True,text=True,check=True)
            self.assertIn("PASS",out.stdout)
    def test_source_payload_size_remains_unchanged(self):
        raw=make_file()
        self.assertEqual(len(raw),24+16*3+1202*33)
        self.assertEqual(struct.unpack_from("<I",raw,12)[0],1202)
        self.assertEqual(struct.unpack_from("<I",raw,16)[0],5000)

if __name__=="__main__":unittest.main()
