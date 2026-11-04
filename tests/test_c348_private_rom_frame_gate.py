"""C348 non-proprietary synthetic XWD and private-ROM evidence tests."""
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c348_private_rom_frame_gate import evidence, inspect_frame


def write_frame(path, *, blank_bottom=False):
    width, height = 256, 384
    head = [0] * 25
    head[0], head[3], head[4], head[5] = 100, 24, width, height
    head[7], head[11], head[12] = 0, 32, width * 4
    head[14:17] = [0xff0000, 0x00ff00, 0x0000ff]
    pixels = bytearray(width * height * 4)
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 4
            if y >= 192 and blank_bottom:
                continue
            if (x // 8 + y // 8) % 2:
                pixels[offset:offset + 4] = bytes((240, 100, 30, 255))
            else:
                pixels[offset:offset + 4] = bytes((30, 220, 220, 255))
    path.write_bytes(struct.pack('>25I', *head) + pixels)


class C348PrivateFrameTests(unittest.TestCase):
    def test_both_screens_and_private_png_evidence(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            rom = root / 'fixture.nds'
            rom.write_bytes(b'DS' * 1024)
            frame = root / 'startup.xwd'
            write_frame(frame)
            screens = inspect_frame(frame)
            self.assertEqual(len(screens), 2)
            self.assertTrue(all(s['unique_sampled_colors'] == 2 for s in screens))
            result = evidence(rom, [frame], root / 'private-evidence')
            self.assertTrue(result['both_ds_screens_nonblank'])
            self.assertFalse(result['original_3ds_screen_parity_verified'])
            self.assertFalse(result['release_ready'])
            self.assertTrue((root / 'private-evidence/startup.png').read_bytes().startswith(b'\x89PNG'))
            self.assertEqual(len(json.loads((root / 'private-evidence/manifest.json').read_text())['frames']), 1)

    def test_blank_lower_screen_rejected_without_artifacts(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            rom = root / 'fixture.nds'
            rom.write_bytes(b'DS' * 1024)
            frame = root / 'startup.xwd'
            write_frame(frame, blank_bottom=True)
            with self.assertRaisesRegex(ValueError, 'blank/unpainted'):
                evidence(rom, [frame], root / 'evidence')
            self.assertFalse((root / 'evidence').exists())

    def test_existing_destination_not_overwritten(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            rom = root / 'fixture.nds'; rom.write_bytes(b'R' * 1024)
            frame = root / 'startup.xwd'; write_frame(frame)
            out = root / 'evidence'; out.mkdir(); (out / 'keep').write_text('untouched')
            with self.assertRaisesRegex(ValueError, 'output must'):
                evidence(rom, [frame], out)
            self.assertEqual((out / 'keep').read_text(), 'untouched')

    def test_bad_names_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            rom = root / 'fixture.nds'; rom.write_bytes(b'R' * 1024)
            frame = root / 'startup.xwd'; write_frame(frame)
            unsafe = root / 'bad name.xwd'; unsafe.write_bytes(frame.read_bytes())
            with self.assertRaisesRegex(ValueError, 'unsafe XWD'):
                evidence(rom, [unsafe], root / 'evidence')
            alias = root / 'linked.xwd'; alias.symlink_to(frame)
            with self.assertRaisesRegex(ValueError, 'unsafe or oversized'):
                inspect_frame(alias)

    def test_corrupt_xwd_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            frame = root / 'startup.xwd'
            frame.write_bytes(b'x' * 500)
            with self.assertRaises(ValueError):
                inspect_frame(frame)


if __name__ == '__main__':
    unittest.main()
