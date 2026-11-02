"""C276 synthetic original texture source-byte SHA and catalog coverage gates."""
import csv
import hashlib
import pathlib
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from c276_private_source_texture_coverage import verify_model, read_catalog, audit
from test_c275_private_draw_material_chain import fixture


def synthetic():
    raw, _ = fixture()
    return raw, [(0, 16, hashlib.sha256(raw[:16]).hexdigest()),
                 (16, 16, hashlib.sha256(raw[16:32]).hexdigest())]


def catalog(folder, records):
    path = folder / "C73.csv"
    with path.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=[
            "model_id", "index", "source_offset", "source_bytes", "sha256", "provenance"])
        writer.writeheader()
        for i, (off, size, sha) in enumerate(records):
            writer.writerow(dict(model_id="p200", index=i, source_offset=off, source_bytes=size,
                                 sha256=sha, provenance="C5_byte_exact"))
    return path


def archives(folder, raw):
    for part in (1, 2, 3):
        with zipfile.ZipFile(folder / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip", "w") as z:
            if part == 1:
                z.writestr("decoded_c5/p200.c5", raw)


class C276Tests(unittest.TestCase):
    def test_exact_original_source_hashes(self):
        raw, rows = synthetic()
        self.assertEqual(verify_model("p200", raw, dict(enumerate(rows)))["source_hash_verified"], 2)

    def test_partial_coverage_is_not_full_fidelity(self):
        raw, rows = synthetic()
        one = verify_model("p200", raw, {0: rows[0]})
        self.assertEqual(one["missing_source_texture_indices"], 1)
        none = verify_model("p200", raw, {})
        self.assertEqual(none["missing_source_texture_indices"], 2)

    def test_mismatch_and_invalid_ranges_fail_closed(self):
        raw, rows = synthetic()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_model("p200", raw, {0: (0, 16, "0" * 64)})
        with self.assertRaisesRegex(ValueError, "outside C5"):
            verify_model("p200", raw, {0: (len(raw) - 1, 16, rows[0][2])})
        with self.assertRaisesRegex(ValueError, "valid source prefix"):
            verify_model("p200", raw, {1: rows[1]})

    def test_private_catalog_duplicate_index_rejected(self):
        raw, rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            path = catalog(folder, rows)
            with path.open("a") as fp:
                fp.write("p200,0,0,16," + rows[0][2] + ",C5_byte_exact\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                read_catalog(path)

    def test_private_catalog_unverified_provenance_rejected(self):
        raw, rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            path = catalog(folder, rows)
            path.write_text(path.read_text().replace("C5_byte_exact", "GUESS"))
            with self.assertRaisesRegex(ValueError, "provenance"):
                read_catalog(path)

    def test_bounded_private_batch_and_full_roster(self):
        raw, rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            archives(folder, raw)
            path = catalog(folder, rows)
            result = audit(folder, path)
            self.assertEqual(result["summary"]["source_c5_texture_bytes_sha_verified"], 2)
            self.assertEqual(result["summary"]["source_texture_indices_missing_from_c73"], 0)
            self.assertEqual(result["summary"]["verified_gpu_sampler_roles"], 0)
            with self.assertRaisesRegex(ValueError, "730"):
                audit(folder, path, require_full=True)


if __name__ == "__main__":
    unittest.main()
