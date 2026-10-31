"""C80 parity inventory and release-gate regressions using repository-owned fixtures."""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from check_feature_parity import check

class ParityGateTests(unittest.TestCase):
    def test_all_required_features_present(self):
        data=check(ROOT/"docs"/"C80_FEATURE_PARITY.json",ROOT)
        self.assertGreaterEqual(len(data["features"]),20)
        self.assertIn("records",{r["id"] for r in data["features"]})
    def test_release_gate_refuses_incomplete_game(self):
        result=subprocess.run([sys.executable,str(ROOT/"tools"/"check_feature_parity.py"),
            str(ROOT/"docs"/"C80_FEATURE_PARITY.json"),"--release"],
            text=True,capture_output=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn("FAILED",result.stderr)
    def test_audit_mode_succeeds_and_reports_gaps(self):
        result=subprocess.run([sys.executable,str(ROOT/"tools"/"check_feature_parity.py"),
            str(ROOT/"docs"/"C80_FEATURE_PARITY.json")],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("challenges",result.stdout)
    def test_cannot_claim_complete_without_end_to_end_evidence(self):
        data=json.loads((ROOT/"docs"/"C80_FEATURE_PARITY.json").read_text())
        entry=data["features"][0]
        entry["status"]="verified_complete"
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/"bad.json"
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):check(p,ROOT)
    def test_required_feature_cannot_be_omitted(self):
        data=json.loads((ROOT/"docs"/"C80_FEATURE_PARITY.json").read_text())
        data["features"]=[row for row in data["features"] if row["id"]!="original_localizations"]
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/"missing.json"
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):check(p,ROOT)
    def test_duplicate_feature_id_rejected(self):
        data=json.loads((ROOT/"docs"/"C80_FEATURE_PARITY.json").read_text())
        data["features"].append(copy.deepcopy(data["features"][0]))
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/"duplicate.json"
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):check(p,ROOT)

if __name__=="__main__": unittest.main()
