"""Synthetic X11 lifecycle regressions: never pass a stale Qt window ID."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HELPER = Path(__file__).with_name("c260_melonds_window.sh")

class LiveWindowTests(unittest.TestCase):
    def exercise(self, windows, failing_xwd=()):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            bin_dir = d / "bin"
            bin_dir.mkdir()
            (d / "windows").write_text("\n".join(windows) + "\n")
            (d / "counter").write_text("0")
            (d / "bad").write_text("\n".join(failing_xwd))
            xwininfo = bin_dir / "xwininfo"
            xwininfo.write_text("""#!/usr/bin/env python3
import pathlib,sys
p=pathlib.Path(__file__).resolve().parent.parent
windows=(p/'windows').read_text().splitlines()
if sys.argv[1:]==['-root','-tree']:
 n=int((p/'counter').read_text()); (p/'counter').write_text(str(n+1))
 w=windows[min(n,len(windows)-1)]
 print('  '+w+' "[60/60] melonDS 1.1"') if w!='none' else None
 sys.exit(0)
if sys.argv[1]=='-id':
 sys.exit(0 if sys.argv[2] in windows and sys.argv[2]!='none' else 1)
sys.exit(1)
""")
            xwd = bin_dir / "xwd"
            xwd.write_text("""#!/usr/bin/env python3
import pathlib,sys
p=pathlib.Path(__file__).resolve().parent.parent
ident=sys.argv[sys.argv.index('-id')+1]
if ident in (p/'bad').read_text().splitlines():sys.exit(1)
pathlib.Path(sys.argv[sys.argv.index('-out')+1]).write_bytes(b'synthetic-xwd')
""")
            for cmd in (xwininfo, xwd):
                cmd.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
            output = d / "home.xwd"
            script = 'source "$1"; p3d_melonds_capture_live_window "$2" 3 "$3"'
            run = subprocess.run(["bash", "-c", script, "bash", str(HELPER),
                                  str(output), str(d / "tree")],
                                 env=env, capture_output=True, text=True)
            return run.returncode, run.stdout.strip(), output.read_bytes() if output.exists() else None

    def test_stale_window_replaced_during_startup(self):
        self.assertEqual(self.exercise(["0x100001", "0x400007"], ("0x100001",)),
                         (0, "0x400007", b"synthetic-xwd"))

    def test_first_window_capture_succeeds(self):
        self.assertEqual(self.exercise(["0x200003"]),
                         (0, "0x200003", b"synthetic-xwd"))

    def test_no_window_fails_closed(self):
        self.assertEqual(self.exercise(["none"]), (1, "", None))

    def test_all_stale_windows_fail_closed(self):
        self.assertEqual(self.exercise(["0x100001", "0x400007"],
                                       ("0x100001", "0x400007")), (1, "", None))

if __name__ == "__main__":
    unittest.main()
