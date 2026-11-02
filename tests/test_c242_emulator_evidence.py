"""Synthetic-only C242 PNG/ROM SHA evidence tests (no Nintendo assets)."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c242_emulator_evidence import xwd_to_png, write_evidence, PNG_SIGNATURE


def make_xwd(path, masks=(0xff0000, 0xff00, 0xff)):
    header = [0] * 25
    header[0], header[1], header[2], header[3] = 100, 7, 2, 24
    header[4], header[5], header[7] = 256, 384, 0
    header[11], header[12] = 32, 256 * 4
    header[14:17] = masks
    path.write_bytes(struct.pack('>25I', *header) + bytes([3, 2, 1, 0]) * (256 * 384))


def png_rows(png):
    assert png.startswith(PNG_SIGNATURE)
    off = 8
    compressed = b''
    while off < len(png):
        size = struct.unpack_from('>I', png, off)[0]
        kind = png[off + 4:off + 8]
        data = png[off + 8:off + 8 + size]
        crc = struct.unpack_from('>I', png, off + 8 + size)[0]
        assert zlib.crc32(kind + data) & 0xffffffff == crc
        if kind == b'IDAT':
            compressed += data
        off += 12 + size
    return zlib.decompress(compressed)


class C242EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.frame = self.root / 'home.xwd'
        make_xwd(self.frame)
        self.rom = self.root / 'smoke.nds'
        self.rom.write_bytes(b'asset-free-only' * 100)
        self.sha = 'a' * 40

    def test_png_channel_order_and_crc(self):
        png = xwd_to_png(self.frame)
        self.assertTrue(png.startswith(PNG_SIGNATURE))
        row = png_rows(png)
        self.assertEqual(row[:4], bytes([0, 1, 2, 3]))
        self.assertEqual(len(row), 384 * (1 + 256 * 3))

    def test_manifest_ties_exact_rom_and_frames(self):
        result = write_evidence(self.rom, self.sha, [self.frame], self.root / 'out')
        self.assertEqual(result['rom_sha256'], hashlib.sha256(self.rom.read_bytes()).hexdigest())
        self.assertEqual(result['frames'][0]['xwd_sha256'], hashlib.sha256(self.frame.read_bytes()).hexdigest())
        saved = json.loads((self.root / 'out/manifest.json').read_text())
        self.assertEqual(saved, result)
        self.assertEqual(result['frames'][0]['png_sha256'], hashlib.sha256((self.root / 'out/home.png').read_bytes()).hexdigest())

    def test_bad_masks_rejected(self):
        make_xwd(self.frame, masks=(0, 0, 0))
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            xwd_to_png(self.frame)

    def test_refuse_unsafe_rom_and_existing_destination(self):
        self.rom.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'refusing'):
            write_evidence(self.rom, self.sha, [self.frame], self.root / 'out')
        self.rom.write_bytes(b'asset-free-only' * 100)
        (self.root / 'out').mkdir()
        with self.assertRaises(FileExistsError):
            write_evidence(self.rom, self.sha, [self.frame], self.root / 'out')

    def test_bad_commit_and_duplicate_frames(self):
        with self.assertRaisesRegex(ValueError, 'source commit'):
            write_evidence(self.rom, 'HEAD', [self.frame], self.root / 'out')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            write_evidence(self.rom, self.sha, [self.frame, self.frame], self.root / 'out')


if __name__ == '__main__':
    unittest.main()
