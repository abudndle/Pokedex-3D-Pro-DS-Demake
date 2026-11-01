"""Synthetic Nintendo DSP-ADPCM source tests; no commercial sound data."""
import struct
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c103_original_cwav_dsp_to_pcm import decode_cwav,decode_dsp_adpcm

def synthetic_cwav(frame=b"\x00"+b"\x78"*7):
    data=bytearray(256)
    data[:4]=b"CWAV";data[4:6]=b"\xff\xfe"
    struct.pack_into("<HIIH",data,6,64,0x02010000,len(data),2)
    struct.pack_into("<HHII",data,0x14,0x7000,0,0x40,0x80)
    struct.pack_into("<HHII",data,0x20,0x7001,0,0xc0,0x40)
    data[0x40:0x44]=b"INFO"
    struct.pack_into("<I",data,0x44,0x80)
    data[0x48]=2
    struct.pack_into("<III",data,0x4c,32000,0,14)
    struct.pack_into("<I",data,0x5c,1)
    struct.pack_into("<HHI",data,0x60,0x7100,0,12)
    struct.pack_into("<HHI",data,0x68,0x1f00,0,0x18)
    struct.pack_into("<HHI",data,0x70,0x0300,0,0x14)
    data[0xc0:0xc4]=b"DATA"
    struct.pack_into("<I",data,0xc4,0x40)
    data[0xe0:0xe8]=frame
    return bytes(data)

class C103Tests(unittest.TestCase):
    def test_exact_original_dsp_nibble_math(self):
        rate,channels,count,pcm=decode_cwav(synthetic_cwav())
        self.assertEqual((rate,channels,count),(32000,1,14))
        self.assertEqual(struct.unpack("<14h",pcm),(7,-8)*7)
    def test_source_coeff_history_used(self):
        output=decode_dsp_adpcm(b"\x00"+b"\x70"*7,[1024,0]+[0]*14,14)
        self.assertEqual(output[0],7)
        self.assertLess(output[1],output[0])
    def test_bad_dsp_predictor_fails(self):
        with self.assertRaisesRegex(ValueError,"predictor"):
            decode_cwav(synthetic_cwav(b"\x80"+bytes(7)))
    def test_unsupported_source_codec_rejected(self):
        data=bytearray(synthetic_cwav())
        data[0x48]=1
        with self.assertRaisesRegex(ValueError,"codec"):
            decode_cwav(data)
    def test_invalid_original_channel_reference_fails(self):
        data=bytearray(synthetic_cwav())
        struct.pack_into("<H",data,0x68,0xffff)
        with self.assertRaisesRegex(ValueError,"reference"):
            decode_cwav(data)
    def test_truncated_source_sample_data_rejected(self):
        data=bytearray(synthetic_cwav())
        struct.pack_into("<I",data,0x54,70)
        with self.assertRaisesRegex(ValueError,"outside DATA"):
            decode_cwav(data)
    def test_no_unbounded_source_decoding(self):
        with self.assertRaisesRegex(ValueError,"sample length"):
            decode_dsp_adpcm(b"",[0]*16,1000001)
if __name__=="__main__":unittest.main()
