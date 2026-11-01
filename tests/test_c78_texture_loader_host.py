#!/usr/bin/env python3
"""Host test of the exact native P3PX v1/v2 reader using synthetic pixels only."""
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DRIVER = r'''
#include "texture_pixels.h"
#include <assert.h>
#include <stdint.h>
int main(int argc,char **argv){
    static P3DTexturePixels pixels;
    assert(argc==7);
    assert(p3dTexturePixelsLoad(&pixels,argv[1]));
    assert(pixels.ready && pixels.width==8 && pixels.height==8 && pixels.version==1);
    assert(pixels.pixels[0]==0x7fff);
    assert(p3dTexturePixelsLoad(&pixels,argv[2]));
    assert(pixels.ready && pixels.version==2 && pixels.pixels[0]==0x1234 && pixels.pixels[1]==0x9234);
    for(int i=3;i<7;i++){
        assert(!p3dTexturePixelsLoad(&pixels,argv[i]));
        assert(!pixels.ready && !pixels.width && !pixels.height && !pixels.version);
    }
    return 0;
}
'''

def texture(version, values, width=8, height=8):
    return struct.pack('<4sHHH', b'P3PX',version,width,height) + struct.pack('<%dH' % len(values),*values)

class C78NativeAlphaReader(unittest.TestCase):
    def test_alpha_transparency_and_fail_closed(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('C compiler unavailable')
        with tempfile.TemporaryDirectory() as d:
            temp = pathlib.Path(d)
            good_v1=texture(1,[0x7fff]*64)
            good_v2=texture(2,[0x1234,0x9234]+[0xffff]*62)
            fixtures=[good_v1,good_v2,
                      texture(3,[0x7fff]*64),
                      good_v2[:-2],
                      good_v2+b'\\x01',
                      texture(2,[0xffff]*64,width=7)]
            # The trailing byte case is a literal single byte, not an encoded escape.
            fixtures[4]=good_v2+bytes([1])
            paths=[]
            for i,data in enumerate(fixtures):
                path=temp/('fixture_%d.p3px'%i)
                path.write_bytes(data)
                paths.append(str(path))
            (temp/'driver.c').write_text(DRIVER)
            executable=temp/'native_test'
            subprocess.run([compiler,'-std=c11','-Wall','-Wextra','-Werror',
                            '-I'+str(ROOT/'source'),
                            str(ROOT/'source'/'texture_pixels.c'),
                            str(temp/'driver.c'),'-o',str(executable)],check=True)
            subprocess.run([str(executable),*paths],check=True)

if __name__=='__main__':
    unittest.main()
