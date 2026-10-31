import tempfile
import unittest
from pathlib import Path
from verify_private_cci import validate

class TestCCI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'synthetic.cci'
        data = bytearray(4096)
        data[0x100:0x104] = b'NCSD'
        data[0x104:0x108] = (8).to_bytes(4, 'little')
        data[0x120:0x124] = (2).to_bytes(4, 'little')
        data[0x124:0x128] = (4).to_bytes(4, 'little')
        data[0x500:0x504] = b'NCCH'
        self.path.write_bytes(data)

    def test_valid(self):
        self.assertEqual(validate(self.path)['validation'], 'PASS')
    def test_missing_ncch(self):
        data = bytearray(self.path.read_bytes()); data[0x500:0x504] = b'NONE'; self.path.write_bytes(data)
        with self.assertRaises(ValueError): validate(self.path)
    def test_out_of_bounds(self):
        data = bytearray(self.path.read_bytes()); data[0x124:0x128] = (20).to_bytes(4, 'little'); self.path.write_bytes(data)
        with self.assertRaises(ValueError): validate(self.path)
    def test_invalid_header(self):
        data = bytearray(self.path.read_bytes()); data[0x100:0x104] = b'FAIL'; self.path.write_bytes(data)
        with self.assertRaises(ValueError): validate(self.path)

if __name__ == '__main__': unittest.main()
