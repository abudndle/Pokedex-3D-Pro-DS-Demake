"""C133: asset-free structural regression for recovered C56 decoder tools."""
import pathlib
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from c5_dual_table_parser import parse
from native_z5_decoder import DecodeError, build_table, decode_stream
from resume_parallel import existing_result
from validate_c56 import assess, validate_source


def synthetic_c5(*, reserved1=0, second_count=2):
    """Construct bounded synthetic C5 descriptors; contains no game assets."""
    data = bytearray(0xa0)
    data[:2] = b"\xc5\x78"
    struct.pack_into("<H", data, 0x14, 1)
    struct.pack_into("<H", data, 0x16, 1)
    for at, value in ((0x3c, 0x78), (0x40, 0x8c), (0x44, 0x98),
                      (0x48, 0x98), (0x4c, 0x98)):
        struct.pack_into("<I", data, at, value)
    struct.pack_into("<5I", data, 0x78, 0x98, 0,
                     (4 << 16) | 1, 0, reserved1)
    struct.pack_into("<3I", data, 0x8c, 0x9c, 0,
                     (2 << 16) | second_count)
    return bytes(data)


class C133Tests(unittest.TestCase):
    def test_strict_original_descriptor_shape(self):
        raw = synthetic_c5()
        status, flags, serious, info = assess(raw)
        self.assertEqual((status, flags, serious), ("strict_valid", 0, []))
        self.assertTrue(info["structural_checks_passed"])
        self.assertEqual(len(info["first_table"]), 1)
        self.assertTrue(info["direct_index_hypothesis_checks"][0][
            "direct_triangle_index_interpretation_valid"])

    def test_unidentified_0x26_is_warning_not_finished_model(self):
        status, flags, serious, info = assess(synthetic_c5(reserved1=0x26))
        self.assertEqual(status, "valid_with_0x26_flag_warning")
        self.assertEqual(flags, 1)
        self.assertFalse(serious)
        self.assertFalse(info["structural_checks_passed"])
        self.assertEqual(assess(synthetic_c5(reserved1=0x27))[0], "invalid")

    def test_truncation_and_bad_table_bounds(self):
        with self.assertRaises(ValueError):
            parse(synthetic_c5()[:32])
        invalid = bytearray(synthetic_c5())
        struct.pack_into("<I", invalid, 0x40, 0xfffffff0)
        with self.assertRaisesRegex(ValueError, "invalid second_table_offset"):
            parse(bytes(invalid))
        # An empty index candidate must not divide by zero.
        self.assertTrue(parse(synthetic_c5(second_count=0))["structural_checks_passed"])

    def test_decoder_rejects_invalid_bounded_streams(self):
        with self.assertRaises(DecodeError):
            decode_stream(b"")
        with self.assertRaisesRegex(DecodeError, "extended output"):
            decode_stream(b"\x40\x00\x00\x00")
        with self.assertRaisesRegex(DecodeError, "safety limit"):
            decode_stream(b"\x40\xff\xff\xff", max_output=1024)
        with self.assertRaises(DecodeError):
            build_table(b"\x03", 0, 9)

    def test_existing_model_must_revalidate(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = pathlib.Path(folder)
            source = folder / "p000.z5"
            output = folder / "p000.c5"
            source.write_bytes(b"x" * 33)
            output.write_bytes(b"not a model" * 20)
            self.assertIsNone(existing_result(source, output))
            output.write_bytes(synthetic_c5())
            row = existing_result(source, output)
            self.assertEqual(row["status"], "existing_strict_valid")
            self.assertEqual(row["bytes"], len(synthetic_c5()))
            # Already-decoded content gets structural review, not blind reuse.
            self.assertEqual(validate_source(source, output)[1], "strict_valid")


if __name__ == "__main__":
    unittest.main()
