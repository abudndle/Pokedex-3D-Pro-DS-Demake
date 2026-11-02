"""C223 private report writer security contract; synthetic data only."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import c151_original_track_bindings as c151

class PrivateAnimationReportTests(unittest.TestCase):
    def test_write_private_report_atomically_with_restricted_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'audit.json'
            result={'source_models_sha_verified':730,'private_package_only':True}
            c151.write_private_report(target,result)
            self.assertEqual(json.loads(target.read_text()),result)
            self.assertEqual(target.stat().st_mode & 0o777,0o600)
            self.assertFalse(list(Path(directory).glob('.c151-report-*.tmp')))

    def test_refuse_report_inside_repository(self):
        target=ROOT/'private-audit-must-not-exist.json'
        with self.assertRaisesRegex(ValueError,'outside public repository'):
            c151.write_private_report(target,{'private_package_only':True})
        self.assertFalse(target.exists())

    def test_refuse_symlink_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'audit.json'
            linked=Path(directory)/'linked.json'
            target.write_text('keep')
            linked.symlink_to(target)
            with self.assertRaisesRegex(ValueError,'symlink'):
                c151.write_private_report(linked,{'private_package_only':True})
            self.assertEqual(target.read_text(),'keep')

    def test_replace_existing_report_without_following_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'audit.json'
            target.write_text('old')
            c151.write_private_report(target,{'generation':2})
            self.assertEqual(json.loads(target.read_text()),{'generation':2})
            self.assertEqual(target.stat().st_mode & 0o777,0o600)

if __name__=='__main__':
    unittest.main()
