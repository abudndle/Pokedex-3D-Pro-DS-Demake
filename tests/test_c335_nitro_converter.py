"""C335: source-verified converter contracts (synthetic source bytes only)."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'tests'))
from c335_private_nitro_engine_stage import export_obj,manifest_bytes,check_evidence
from test_c211_private_source_pair import pair

def source_pair(model=25):
    vx,ix=pair(model=model)
    b=bytearray(vx)
    offset=16+8
    for i,coords in enumerate(((0,0,0),(4096,0,0),(0,4096,0),(0,0,4096))):
        struct.pack_into('<3h',b,offset+i*6,*coords)
    struct.pack_into('<I',b,12,zlib.crc32(b[16:]))
    return bytes(b),ix

def report():
    return {'schema':'p3d-c245-private-ordered-source-geometry-pair-v1',
      'source_c5_face_bytes_exact_unique':True,
      'source_c5_xyz_order_exact':True,
      'native_p3vx_p3ix_pair_valid':True,
      'mesh_count':1,'vertex_count':4,'triangle_count':2,
      'complete_original_model_verified':False}

class ConversionTests(unittest.TestCase):
    def test_original_triangle_order_and_geometry_not_reinvented(self):
        vx,ix=source_pair()
        obj=export_obj(vx,ix,25)
        self.assertIn('v 1 0 0',obj)
        self.assertIn('v 0 1 0',obj)
        self.assertIn('g source_mesh_2',obj)
        self.assertEqual([l for l in obj.splitlines() if l.startswith('f ')],
                         ['f 1 2 3','f 2 3 4'])
        self.assertEqual(sum(l.startswith('v ') for l in obj.splitlines()),4)
        self.assertNotIn('vt ',obj) # source UV/material not recovered

    def test_distinct_original_model_identity_rejected(self):
        vx,ix=source_pair()
        with self.assertRaisesRegex(ValueError,'identity'):
            export_obj(vx,ix,26)

    def test_invalid_original_face_ownership_rejected(self):
        vx,ix=source_pair()
        ix=bytearray(ix);struct.pack_into('<H',ix,16,99)
        with self.assertRaisesRegex(ValueError,'vertex ownership'):
            export_obj(vx,bytes(ix),25)

    def test_source_crc_required(self):
        vx,ix=source_pair()
        vx=bytearray(vx);vx[-1]^=1
        with self.assertRaisesRegex(ValueError,'CRC'):
            export_obj(bytes(vx),ix,25)

    def test_static_display_list_manifest_binds_both_source_files(self):
        vx,ix=source_pair()
        dl=struct.pack('<3I',2,0x40000040,0x00000041)
        m=manifest_bytes(vx,ix,25,dl)
        self.assertEqual(len(m),36)
        self.assertEqual(m[:4],b'P3NE')
        self.assertEqual(m[5],1)
        self.assertEqual(struct.unpack_from('<H',m,6)[0],25)
        self.assertEqual(struct.unpack_from('<I',m,8)[0],zlib.crc32(vx))
        self.assertEqual(struct.unpack_from('<I',m,12)[0],zlib.crc32(ix))
        self.assertEqual(struct.unpack_from('<I',m,20)[0],zlib.crc32(dl))
        self.assertEqual(struct.unpack_from('<I',m,32)[0],zlib.crc32(m[:32]))

    def test_malformed_display_lists_fail_closed(self):
        vx,ix=source_pair()
        for dl in (b'',b'NOPE',struct.pack('<2I',2,0),b'\x00'*9):
            with self.subTest(size=len(dl)),self.assertRaises(ValueError):
                manifest_bytes(vx,ix,25,dl)

    def test_private_evidence_requires_original_xyz_and_exact_faces(self):
        r=report()
        check_evidence(json.dumps(r).encode(),25,
            {'vertex_meshes':1,'triangles':2,'vertices':4})
        for field in ('source_c5_face_bytes_exact_unique',
                      'source_c5_xyz_order_exact',
                      'native_p3vx_p3ix_pair_valid'):
            bad=dict(r);bad[field]=False
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'proof'):
                check_evidence(json.dumps(bad).encode(),25,
                    {'vertex_meshes':1,'triangles':2,'vertices':4})
        with self.assertRaisesRegex(ValueError,'proof'):
            check_evidence(json.dumps(r).encode(),25,
                {'vertex_meshes':1,'triangles':3,'vertices':4})

if __name__=='__main__':
    unittest.main()
