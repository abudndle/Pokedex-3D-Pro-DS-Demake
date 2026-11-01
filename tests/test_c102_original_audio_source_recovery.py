"""Synthetic Nintendo audio-container source validation; no copyrighted bytes."""
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c102_original_audio_source_recovery import KINDS,validate_header,recover

def make_audio(kind):
    b=bytearray(64+16*len(KINDS[kind]))
    b[:4]=kind
    b[4:6]=b"\xff\xfe"
    struct.pack_into("<HIIH",b,6,64,0x02010000,len(b),len(KINDS[kind]))
    for i,section in enumerate(KINDS[kind]):
        struct.pack_into("<HHII",b,20+i*12,section,0,64+16*i,16)
        b[64+16*i:80+16*i]=bytes([i+1])*16
    return bytes(b)

class OriginalSoundSourceTests(unittest.TestCase):
    def test_all_four_header_section_types(self):
        for kind in KINDS:
            blob=make_audio(kind)
            result=validate_header(blob,0,kind)
            self.assertIsNotNone(result)
            self.assertEqual(result["size"],len(blob))
    def test_bogus_section_size_rejected(self):
        blob=bytearray(make_audio(b"CWAV"))
        struct.pack_into("<I",blob,20+8,0xfffffff0)
        self.assertIsNone(validate_header(blob,0,b"CWAV"))
    def test_bad_bom_and_overlapping_sections_rejected(self):
        blob=bytearray(make_audio(b"CSTM"))
        blob[4:6]=b"\xfe\xff"
        self.assertIsNone(validate_header(blob,0,b"CSTM"))
        blob=bytearray(make_audio(b"CSTM"))
        struct.pack_into("<I",blob,20+12+4,64)
        self.assertIsNone(validate_header(blob,0,b"CSTM"))
    def test_spoofed_magic_not_valid_audio(self):
        self.assertIsNone(validate_header(b"CWAV"+bytes(200),0,b"CWAV"))
    def test_extract_only_source_headers_to_private_zip(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            image=root/"synthetic.cci"
            image.write_bytes(b"x"*96+make_audio(b"CWAV")+b"x"*32+make_audio(b"CSTM"))
            out=root/"audio.zip";report=root/"report.json"
            result=recover(image,out,report)
            self.assertEqual(result["format_counts"],{"CWAV":1,"CSTM":1})
            self.assertEqual(result["audio_containers"],2)
            self.assertFalse(result["Nintendo_DS_audio_playback_implemented"])
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(len(z.namelist()),3)
            self.assertEqual(json.loads(report.read_text())["audio_containers"],2)
    def test_never_overwrite_private_source(self):
        with tempfile.TemporaryDirectory() as d:
            source=pathlib.Path(d)/"original.cci";source.write_bytes(make_audio(b"CWAV"))
            with self.assertRaisesRegex(ValueError,"overwrite"):
                recover(source,source,pathlib.Path(d)/"report.json")
if __name__=="__main__":unittest.main()
