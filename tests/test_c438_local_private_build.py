"""C438 argument-handling tests for the local private build script; no assets."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'c438_local_private_build.sh'


def run(*args):
    return subprocess.run(['bash', str(SCRIPT), *args], capture_output=True, text=True)


class LocalPrivateBuildArgs(unittest.TestCase):
    def test_requires_zip(self):
        r = run()
        self.assertEqual(r.returncode, 2)
        self.assertIn('--nitrofs-zip is required', r.stderr)

    def test_missing_zip_fails(self):
        r = run('--nitrofs-zip', '/nonexistent/package.zip')
        self.assertEqual(r.returncode, 2)
        self.assertIn('not found', r.stderr)

    def test_manifest_needs_asset_root(self):
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / 'a.zip'
            z.write_bytes(b'')
            m = Path(d) / 'm.json'
            m.write_text('{}')
            r = run('--nitrofs-zip', str(z), '--manifest', str(m))
        self.assertEqual(r.returncode, 2)
        self.assertIn('--asset-root', r.stderr)

    def test_missing_option_values(self):
        for flag in ('--nitrofs-zip', '--manifest', '--asset-root', '--stage-dir'):
            with self.subTest(flag=flag):
                result = run(flag)
                self.assertEqual(result.returncode, 2)
                self.assertIn(flag + ' requires a value', result.stderr)

    def test_missing_option_value_does_not_consume_next_flag(self):
        result = run('--nitrofs-zip', '--skip-host-tests')
        self.assertEqual(result.returncode, 2)
        self.assertIn('--nitrofs-zip requires a value', result.stderr)

    def test_help(self):
        r = run('--help')
        self.assertEqual(r.returncode, 0)
        self.assertIn('Usage:', r.stderr)


if __name__ == '__main__':
    unittest.main()
