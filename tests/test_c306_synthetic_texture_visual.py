"""C306 synthetic visual acceptance: CRC-packed fixtures and RGB XWD gates."""
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c306_synthetic_texture_stage import stage
from c306_synthetic_texture_frame_gate import verify, safe_png, verify_legacy_mixed
from test_c235_emulator_frame_gate import make_xwd, paint_region


def colored(path, rgb, region=(105, 70, 160, 125)):
    data = bytearray(path.read_bytes())
    x0, y0, x1, y1 = region
    packed = rgb.to_bytes(4, "little")
    for y in range(y0, y1):
        for x in range(x0, x1):
            off = 100 + (y * 256 + x) * 4
            data[off:off + 4] = packed
    path.write_bytes(data)


class C306SyntheticTextureVisualTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="c306-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_stage_exact_synthetic_material_shader_uv_and_pixels(self):
        stage_root = self.root / "fixture"
        stage_root.mkdir()
        out = stage(stage_root)
        self.assertEqual(len(list(out.rglob("*.p3px"))), 4)
        self.assertEqual(len(list(out.rglob("*.p3vu"))), 3)
        self.assertEqual(len(list(out.rglob("*.p3mr"))), 4)
        mapping = (out / "models/species_map.p3sm").read_bytes()
        self.assertEqual(struct.unpack_from("<4H", mapping, 8), (2, 3, 4, 5))
        for model, texture, pixel in ((2, 7, 0x801f), (3, 8, 0xfc00)):
            name = f"p{model:03d}"
            vx = (out / "geometry" / (name + ".p3vx")).read_bytes()
            vu = (out / "geometry" / (name + ".p3vu")).read_bytes()
            self.assertEqual(struct.unpack_from("<I", vu, 12)[0], zlib.crc32(vx))
            self.assertEqual(struct.unpack_from("<I", vu, 16)[0],
                             zlib.crc32(vu[20:]))
            px = (out / "textures" / name / f"t{texture:03d}.p3px").read_bytes()
            self.assertEqual(struct.unpack_from("<H", px, 10)[0], pixel)
            for suffix in ("p3mr", "p3sc", "p3sw"):
                raw = (out / "materials" / (name + "." + suffix)).read_bytes()
                self.assertEqual(struct.unpack_from("<I", raw, 12)[0],
                                 zlib.crc32(raw[16:]))

    def test_only_empty_staging_directory_allowed(self):
        invalid = self.root / "fixture"
        invalid.mkdir()
        (invalid / "surprise").write_text("no")
        with self.assertRaisesRegex(ValueError, "empty"):
            stage(invalid)

    def frames(self):
        paths = [self.root / f"{name}.xwd" for name in ("home", "red", "blue", "back")]
        for p in paths:
            make_xwd(p)
            raw = bytearray(p.read_bytes())
            fields = list(struct.unpack_from(">25I", raw))
            fields[7] = 0
            fields[14:17] = [0xff0000, 0xff00, 0xff]
            raw[:100] = struct.pack(">25I", *fields)
            p.write_bytes(raw)
        colored(paths[1], 0x00ff0000)
        colored(paths[2], 0x000000ff)
        paint_region(paths[1], (133, 38, 145, 49), 255)
        paint_region(paths[2], (125, 38, 137, 49), 255)
        paint_region(paths[1], (86, 295, 96, 304), 255)
        paint_region(paths[2], (76, 295, 86, 304), 255)
        return paths

    def test_two_synthetic_textures_and_png_are_real_color_frames(self):
        paths = self.frames()
        result = verify(*paths)
        self.assertTrue(result["synthetic_native_visual_acceptance"])
        self.assertFalse(result["original_visual_parity_verified"])
        self.assertGreater(result["synthetic_red_pixels"], 100)
        self.assertGreater(result["synthetic_blue_pixels"], 100)
        png = self.root / "capture.png"
        safe_png(paths[1], png)
        self.assertEqual(png.read_bytes()[:8], bytes((137,80,78,71,13,10,26,10)))

    def test_missing_distinct_color_fails(self):
        paths = self.frames()
        colored(paths[2], 0x00ff0000)
        with self.assertRaisesRegex(ValueError, "not visible"):
            verify(*paths)

    def test_legacy_frame_requires_both_texture_and_untextured_face(self):
        legacy = self.frames()[0]
        colored(legacy, 0x00ff0000, (125, 70, 160, 125))
        with self.assertRaisesRegex(ValueError, "green texture"):
            verify_legacy_mixed(legacy)
        colored(legacy, 0x0000ff00, (85, 70, 120, 125))
        result = verify_legacy_mixed(legacy)
        self.assertGreater(result["legacy_green_texture_samples"], 100)
        self.assertGreater(result["legacy_red_face_samples"], 100)
        colored(legacy, 0x0000ff00, (125, 70, 160, 125))
        with self.assertRaisesRegex(ValueError, "red face color"):
            verify_legacy_mixed(legacy)

    def test_forged_non_native_rgb_header_fails(self):
        paths = self.frames()
        data = bytearray(paths[1].read_bytes())
        struct.pack_into(">I", data, 14 * 4, 0)
        paths[1].write_bytes(data)
        with self.assertRaisesRegex(ValueError, "RGB masks"):
            verify(*paths)


if __name__ == "__main__":
    unittest.main()
