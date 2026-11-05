from pathlib import Path
import tempfile
import unittest
import struct
from test_c306_synthetic_texture_visual import colored
from test_c235_emulator_frame_gate import make_xwd
from c359_zoom_frame_gate import verify
def paint(path,rgb,box):
    make_xwd(path)
    b=bytearray(path.read_bytes());struct.pack_into('>III',b,56,0xff0000,0xff00,0xff)
    path.write_bytes(b)
    colored(path,(rgb[0]<<16)|(rgb[1]<<8)|rgb[2],box)


class ZoomGateTests(unittest.TestCase):
    def test_real_size_change_reset_and_wrong_frames(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/f'{i}.xwd' for i in range(5)]
            boxes=((70,60,170,160),(50,40,190,180),(70,60,170,160),(90,80,150,140),(70,60,170,160))
            for p,box in zip(paths,boxes):paint(p,(255,0,0),box)
            self.assertTrue(verify(*paths)['native_zoom_reset_verified'])
            for i in range(5):
                paint(paths[i],(0,0,0),(0,0,256,192))
                with self.assertRaises(ValueError):verify(*paths)
                paint(paths[i],(255,0,0),boxes[i])


if __name__=='__main__':unittest.main()
