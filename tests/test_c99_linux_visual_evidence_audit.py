"""C99 screenshots are source-geometry QA, never fabricated melonDS captures."""
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from c99_linux_visual_evidence_audit import check_png,verify

def chunk(tag,data):
    return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data))

def png():
    row=b"\x00"+bytes((0,32,64,255))*(256*3//4)
    pixels=row*192
    hdr=struct.pack(">IIBBBBB",256,192,8,2,0,0,0)
    return (b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",hdr)+
            chunk(b"IDAT",zlib.compress(pixels))+chunk(b"IEND",b""))

def fixture(root,wrong_claim=False):
    for suffix in ("ds3m","p3cs"):
        (root/("C99_SOFTWARE_QA_p000_"+suffix+".png")).write_bytes(png())
    report={
        "platform":"Linux (Pillow software rasterizer)",
        "tested_emulator":"melonDS" if wrong_claim else "NONE",
        "melonds_test_passed":False,
        "native_arm_rom_compiled_here":False,
        "original_3ds_shader_parity_proven":False,
        "model_screenshots":[{"model_id":"p000","legacy_source_faces":461,
            "chunk_source_faces":1800,"changed_pixels":10226,
            "software_images":["C99_SOFTWARE_QA_p000_ds3m.png",
                               "C99_SOFTWARE_QA_p000_p3cs.png"]}]}
    (root/"C99_LINUX_RENDER_QA_REPORT.json").write_text(json.dumps(report))

class C99Tests(unittest.TestCase):
    def test_synthetic_valid_ds_resolution(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            fixture(root)
            self.assertEqual(verify(root)["software_screenshots"],2)
    def test_c128_reject_duplicate_or_mislabeled_source_views(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            fixture(root)
            report_path=root/"C99_LINUX_RENDER_QA_REPORT.json"
            original=json.loads(report_path.read_text())
            for views in (
                ["C99_SOFTWARE_QA_p000_ds3m.png"]*2,
                ["C99_SOFTWARE_QA_p000_p3cs.png",
                 "C99_SOFTWARE_QA_p000_ds3m.png"],
                ["C99_SOFTWARE_QA_p000_ds3m.png"],
            ):
                report=json.loads(json.dumps(original))
                report["model_screenshots"][0]["software_images"]=views
                report_path.write_text(json.dumps(report))
                with self.assertRaisesRegex(ValueError,"source QA views"):
                    verify(root)
            report_path.write_text(json.dumps(original))
            self.assertEqual(verify(root)["software_screenshots"],2)
    def test_c129_reject_malformed_compressed_visual_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            fixture(root)
            target=root/"C99_SOFTWARE_QA_p000_ds3m.png"
            original=target.read_bytes()
            header=struct.pack(">IIBBBBB",256,192,8,2,0,0,0)
            # CRC-correct but decoded data far exceeds a single DS frame.
            huge=(b"\\x00"+bytes((1,2,3)) *256)*400
            oversized=(b"\\x89PNG\\r\\n\\x1a\\n"+chunk(b"IHDR",header)+
                       chunk(b"IDAT",zlib.compress(huge))+chunk(b"IEND",b""))
            target.write_bytes(oversized)
            with self.assertRaisesRegex(ValueError,"payload size"):
                verify(root)
            # Valid PNG signatures/CRCs must not permit IDAT before IHDR.
            wrong_order=(b"\\x89PNG\\r\\n\\x1a\\n"+
                         chunk(b"IDAT",zlib.compress(b"x"))+
                         chunk(b"IHDR",header)+chunk(b"IEND",b""))
            target.write_bytes(wrong_order)
            with self.assertRaisesRegex(ValueError,"chunk order"):
                verify(root)
            target.write_bytes(original)
            self.assertEqual(verify(root)["software_screenshots"],2)
    def test_corrupt_frame_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            fixture(root)
            target=root/"C99_SOFTWARE_QA_p000_ds3m.png"
            bad=bytearray(target.read_bytes());bad[-8]^=1
            target.write_bytes(bad)
            with self.assertRaises(ValueError):verify(root)
    def test_false_emulator_claim_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            fixture(root,wrong_claim=True)
            with self.assertRaisesRegex(ValueError,"unverified emulator"):
                verify(root)
if __name__=="__main__":unittest.main()
