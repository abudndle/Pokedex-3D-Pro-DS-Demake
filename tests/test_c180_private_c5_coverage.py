import importlib.util
import io
import os
import stat
import tempfile
import zipfile
from unittest import mock
import pathlib
import struct
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("c180",ROOT/"tools/c180_private_c5_coverage.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class C180Coverage(unittest.TestCase):
    def fixture(self):
        data=bytearray(0x90)
        data[:2]=b"\xc5\x78"
        struct.pack_into("<H",data,0x14,1)
        struct.pack_into("<I",data,0x3c,0x78)
        struct.pack_into("<I",data,0x40,0x8c)
        struct.pack_into("<I",data,0x44,0x8c)
        struct.pack_into("<5I",data,0x78,0x8c,0,0x00040001,0,0)
        return data
    def test_valid_structural_fixture(self):
        result=mod.inspect(self.fixture())
        self.assertEqual(result["primary"],1)
        self.assertFalse(result["vertex_semantics_verified"])
    def test_reject_invalid_table_bounds(self):
        data=self.fixture()
        struct.pack_into("<I",data,0x40,0x80)
        with self.assertRaises(ValueError):mod.inspect(data)
    def test_report_invalid_payload(self):
        data=self.fixture()
        struct.pack_into("<I",data,0x78,0xffffffff)
        self.assertTrue(mod.inspect(data)["structural_errors"])
    def archive(self, members):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in members:
                archive.writestr(name, data)
        buffer.seek(0)
        return buffer

    def test_single_model_is_incomplete_not_verified(self):
        report = mod.audit([self.archive([("decoded_c5/p000.c5", self.fixture())])])
        self.assertEqual(report["present"], 1)
        self.assertEqual(len(report["missing"]), 729)
        self.assertFalse(report["all_structural_checks_passed"])
        self.assertFalse(report["topology_verified"])

    def test_noncanonical_model_name_rejected(self):
        archive = self.archive([("decoded_c5/p000_extra.c5", self.fixture())])
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            mod.audit([archive])

    def test_duplicate_model_rejected(self):
        archive = self.archive([("decoded_c5/p000.c5", self.fixture()),
                                ("decoded_c5/p000.c5", self.fixture())])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.audit([archive])

    def test_out_of_roster_model_rejected(self):
        archive = self.archive([("decoded_c5/p721.c5", self.fixture())])
        with self.assertRaisesRegex(ValueError, "out-of-roster"):
            mod.audit([archive])

    def test_oversized_member_fails_without_reading(self):
        archive = self.archive([("decoded_c5/p000.c5", self.fixture())])
        with mock.patch.object(mod, "MAX_C5_BYTES", 16):
            report = mod.audit([archive])
        self.assertEqual(report["structural_failures"], [0])
        self.assertEqual(report["models"]["p000"]["error"], "invalid or oversized C5 member")

    def test_private_report_mode_and_location(self):
        with tempfile.TemporaryDirectory() as directory:
            report = pathlib.Path(directory) / "private" / "report.json"
            mod.write_private_report(report, {"models": {"p000": {"sha256": "synthetic"}}})
            self.assertEqual(stat.S_IMODE(os.stat(report).st_mode), 0o600)
            self.assertIn("synthetic", report.read_text())
        with self.assertRaisesRegex(ValueError, "outside the public repository"):
            mod.write_private_report(ROOT / "c180-private-report.json", {})

if __name__=="__main__":unittest.main()
