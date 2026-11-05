"""Fail-closed C359 geometry tests; synthetic fixtures only."""
import pathlib,struct,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from c359_synthetic_fixtures import source
from c359_gui_vertex_uv_topology import recover_geometry

class TestInvalidGeometry(unittest.TestCase):
    def test_invalid_vertex_format(self):
        raw=bytearray(source('gui_common'))
        p=struct.unpack_from('<I',raw,0x68)[0]
        a=struct.unpack_from('<I',raw,p+0x3c)[0]
        struct.pack_into('<I',raw,p+a+12,0x1234)
        with self.assertRaisesRegex(ValueError,'vertex descriptor'):
            recover_geometry(bytes(raw))

    def test_wrong_16bit_index_format(self):
        raw=bytearray(source('gui_common'))
        p=struct.unpack_from('<I',raw,0x68)[0]
        a=struct.unpack_from('<I',raw,p+0x40)[0]
        struct.pack_into('<H',raw,p+a+10,4)
        with self.assertRaisesRegex(ValueError,'triangle descriptor'):
            recover_geometry(bytes(raw))

    def test_index_beyond_vertex_count(self):
        raw=bytearray(source('gui_common'))
        p=struct.unpack_from('<I',raw,0x68)[0]
        a=struct.unpack_from('<I',raw,p+0x40)[0]
        off=struct.unpack_from('<I',raw,p+a)[0]
        beginning=p+struct.unpack_from('<I',raw,p+4)[0]+120
        struct.pack_into('<H',raw,beginning+off,0xffff)
        with self.assertRaisesRegex(ValueError,'vertex outside'):
            recover_geometry(bytes(raw))

    def test_nan_coordinate(self):
        raw=bytearray(source('gui_common'))
        p=struct.unpack_from('<I',raw,0x68)[0]
        beginning=p+struct.unpack_from('<I',raw,p+4)[0]+120
        struct.pack_into('<f',raw,beginning,float('nan'))
        with self.assertRaisesRegex(ValueError,'vertex XYZ'):
            recover_geometry(bytes(raw))
