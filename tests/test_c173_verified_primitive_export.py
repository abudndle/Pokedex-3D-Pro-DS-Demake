import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from c173_verified_primitive_export import export,MAGIC
from c171_verified_primitive_gate import SCHEMA

def fixture():
    source=bytearray(276)
    source[:2]=bytes((0xc5,0x78))
    struct.pack_into("<H",source,0x10,1)
    struct.pack_into("<HH",source,0x14,1,1)
    struct.pack_into("<3I",source,0x3c,120,140,152)
    struct.pack_into("<5I",source,120,152,0,4|(28<<16),0,0)
    struct.pack_into("<3I",source,140,264,0,6|(2<<16))
    manifest={"schema":SCHEMA,"source":"original-c5",
              "method":"verified-original-primitive-order",
              "verified_by":"source-decoder-crosscheck","model":"p000",
              "meshes":[{"model":"p000","mesh":0,
                         "triangles":[[0,1,2],[1,2,3]]}]}
    return manifest,bytes(source)

class C173Tests(unittest.TestCase):
    def test_export_round_trip(self):
        m,s=fixture();raw=export(m,s)
        self.assertEqual(raw[:4],MAGIC)
        self.assertEqual(struct.unpack_from("<HHH",raw,4),(1,0,1))
        self.assertEqual(struct.unpack_from("<HI",raw,10),(0,2))
        self.assertEqual(struct.unpack_from("<6H",raw,16),(0,1,2,1,2,3))
    def test_partial_map_rejected(self):
        m,s=fixture();m["meshes"][0]["triangles"].pop()
        with self.assertRaises(ValueError):export(m,s)
    def test_wrong_source_model_rejected(self):
        m,s=fixture();m["meshes"][0]["model"]="p001"
        with self.assertRaises(ValueError):export(m,s)
if __name__=="__main__":unittest.main()
