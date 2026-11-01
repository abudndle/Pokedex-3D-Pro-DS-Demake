"""Synthetic source-only tests for C140 C5 shader declaration recovery."""
import csv
import hashlib
import io
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
# Also works when this test is run directly in c140_work locally.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from c140_c5_shader_inventory import audit, parse_declarations, ROSTER, PART_RANGES


def c5(flags=b"CF_TEXTURE,CF_COLORMAP", offset=0x78):
    data = bytearray(max(offset, 0x78))
    data[:2] = b"\xc5\x78"
    struct.pack_into("<I", data, 0x64, offset)
    return bytes(data) + b"kawa;;;" + flags + b"\0shadow;;;CF_WEIGHT,CF_CASTSHADOW\0mesh\0"


def fixture(folder):
    archives = []
    rows = []
    for i, (first, last) in enumerate(PART_RANGES):
        path = folder / ("part%d.zip" % i)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for model in range(first, last + 1):
                if model not in ROSTER:
                    continue
                raw = c5()
                label = "p%03d" % model
                z.writestr("decoded_c5/%s.c5" % label, raw)
                rows.append({"model": label, "decoded_bytes": str(len(raw)),
                             "sha256": hashlib.sha256(raw).hexdigest()})
        archives.append(path)
    bundle = folder / "decoder.zip"
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=("model", "decoded_bytes", "sha256"))
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(bundle, "w") as z:
        z.writestr("C56_validation.csv", output.getvalue())
    return archives, bundle


class C140ShaderRecovery(unittest.TestCase):
    def test_parses_original_header_address_not_arbitrary_texture_names(self):
        result = parse_declarations(c5())
        self.assertEqual([x["program"] for x in result], ["kawa", "shadow"])
        self.assertEqual(result[0]["source_offset"], 0x78)
        self.assertEqual(result[1]["flags"], ["CF_WEIGHT", "CF_CASTSHADOW"])
        self.assertEqual(len(result[0]["source_sha256"]), 64)

    def test_full_source_inventory_remains_unmapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, bundle = fixture(pathlib.Path(tmp))
            result = audit(paths, bundle)
            self.assertEqual(result["models_verified"], 730)
            self.assertEqual(result["shader_declarations_recovered"], 1460)
            self.assertEqual(result["flag_occurrences"]["CF_COLORMAP"], 730)
            self.assertEqual(result["flag_occurrences"]["CF_CASTSHADOW"], 730)
            self.assertEqual(result["certified_original_textured_models"], 0)
            self.assertEqual(result["verified_source_material_to_shader_bindings"], 0)
            self.assertFalse(result["models"]["p000"]["native_texture_binding_ready"])
            self.assertEqual(len(result["models"]), 730)

    def test_reject_corrupt_source_and_swapped_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths, bundle = fixture(pathlib.Path(tmp))
            with self.assertRaisesRegex(ValueError, "out-of-part"):
                audit(paths[::-1], bundle)
            bad = paths[0]
            with zipfile.ZipFile(bad) as z:
                entries = {name: z.read(name) for name in z.namelist()}
            entries["decoded_c5/p000.c5"] += b"z"
            with zipfile.ZipFile(bad, "w") as z:
                for name, payload in entries.items():
                    z.writestr(name, payload)
            with self.assertRaisesRegex(ValueError, "hash/size mismatch"):
                audit(paths, bundle)

    def test_reject_truncated_unknown_and_forged_source_flags(self):
        for invalid in (b"NOTC5", c5(b"WRONG"), c5(b"CF_COLORMAP,CF_COLORMAP"),
                        c5(b"CF_COLORMAP,CF_!DANGEROUS")):
            with self.assertRaises(ValueError):
                parse_declarations(invalid)
        forged = bytearray(c5())
        struct.pack_into("<I", forged, 0x64, 0xffffffff)
        with self.assertRaisesRegex(ValueError, "offset"):
            parse_declarations(bytes(forged))
        self.assertEqual(parse_declarations(c5(b"CF_COLORMAP,CF_BUMPMAP"))[0]
                         ["flags"], ["CF_COLORMAP", "CF_BUMPMAP"])


if __name__ == "__main__":
    unittest.main()