"""Synthetic-only tests for the private source-archive recovery audit."""
import pathlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from audit_private_recovery_workspace import audit, REQUIRED

class RecoveryAuditTests(unittest.TestCase):
    def test_missing_all_archives(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=audit(pathlib.Path(tmp))
            self.assertFalse(result["complete"])
            self.assertEqual(len(result["missing"]),sum(map(len,REQUIRED.values())))
            self.assertFalse(result["invalid"])
    def test_valid_and_corrupt_archives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            for group,names in REQUIRED.items():
                folder=root/group
                folder.mkdir()
                for name in names:
                    with zipfile.ZipFile(folder/name,"w") as z:
                        z.writestr("fixture.txt",b"safe synthetic data")
            self.assertTrue(audit(root)["complete"])
            target=root/"recovery"/REQUIRED["recovery"][0]
            target.write_bytes(b"not a ZIP")
            result=audit(root)
            self.assertFalse(result["complete"])
            self.assertEqual(result["invalid"],[target.name])
    def test_reject_duplicate_members_and_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            folder=root/"packages"
            folder.mkdir()
            path=folder/REQUIRED["packages"][0]
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",UserWarning)
                with zipfile.ZipFile(path,"w") as z:
                    z.writestr("same",b"a")
                    z.writestr("same",b"b")
            self.assertIn(path.name,audit(root)["invalid"])
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("../escape",b"bad")
            self.assertIn(path.name,audit(root)["invalid"])
if __name__=="__main__":
    unittest.main()
