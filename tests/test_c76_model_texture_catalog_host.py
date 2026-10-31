#!/usr/bin/env python3
"""Synthetic P3TM C-loader regression test; uses no commercial game assets."""
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = ROOT / "source" if (ROOT / "source" / "model_texture_catalog.c").exists() else pathlib.Path(__file__).resolve().parent
C_DRIVER = r'''
#include "model_texture_catalog.h"
#include <assert.h>
#include <string.h>
int main(int argc, char **argv) {
    P3DModelTextureCatalog c;
    assert(argc == 3);
    assert(p3dTextureCatalogLoad(&c, argv[1], 3));
    assert(c.ready && c.model_id==3 && c.texture_count==1);
    assert(c.entries[0].width==128 && c.entries[0].height==64);
    assert(strcmp(c.entries[0].original_name, "fixture_diffuse")==0);
    assert(!p3dTextureCatalogLoad(&c, argv[1], 4));
    assert(!c.ready);
    assert(!p3dTextureCatalogLoad(&c, argv[2], 3));
    assert(!c.ready);
    return 0;
}
'''

def fixture():
    name = b'fixture_diffuse'
    body = struct.pack('<HHHII32sH',0,128,64,0x12345678,4567,b'\x0b'*32,len(name))+name
    head = struct.pack('<4sHHHHII',b'P3TM',1,3,1,0,len(body),zlib.crc32(body))
    return head+body

class TestC76Loader(unittest.TestCase):
    def test_synthetic_catalog_and_crc_failure(self):
        cc = shutil.which('cc')
        if cc is None:
            self.skipTest('C compiler unavailable')
        with tempfile.TemporaryDirectory() as d:
            tmp = pathlib.Path(d)
            (tmp/'driver.c').write_text(C_DRIVER)
            good = fixture()
            (tmp/'good.p3tm').write_bytes(good)
            bad = bytearray(good); bad[-1] ^= 1
            (tmp/'bad.p3tm').write_bytes(bad)
            subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror',
                            '-I'+str(SOURCES),str(SOURCES/'model_texture_catalog.c'),
                            str(tmp/'driver.c'),'-o',str(tmp/'c76_test')],check=True)
            subprocess.run([str(tmp/'c76_test'),str(tmp/'good.p3tm'),str(tmp/'bad.p3tm')],check=True)

if __name__=='__main__':unittest.main()
