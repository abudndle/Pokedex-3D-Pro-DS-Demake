#!/usr/bin/env python3
"""C348: capture real DeSmuME dual-screen XWD frames from a PRIVATE build.

Call this only inside the private asset repository Actions runner under Xvfb.
The native `.nds` ROM may contain proprietary source resources.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def capture(rom: Path, out: Path):
    if not os.environ.get('DISPLAY'):
        raise ValueError('X11 DISPLAY required (use xvfb-run)')
    if out.exists() or not out.parent.is_dir():
        raise ValueError('private frame output directory must not exist')
    binary = shutil.which('desmume-cli')
    if not binary and Path('/usr/games/desmume-cli').is_file():
        binary = '/usr/games/desmume-cli'
    if not binary:
        raise ValueError('DeSmuME CLI not installed')
    if not rom.is_file() or rom.is_symlink():
        raise ValueError('missing or unsafe private NDS ROM')
    out.mkdir(mode=0o700)
    with (out / 'emulator.log').open('wb') as log:
        proc = subprocess.Popen([binary, '--disable-sound', str(rom)],
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            window = None
            for _ in range(40):
                if proc.poll() is not None:
                    raise RuntimeError('DeSmuME exited before a window appeared')
                result = subprocess.run(['xwininfo', '-root', '-tree'], capture_output=True,
                                        text=True, check=True, timeout=5)
                for line in result.stdout.splitlines():
                    if '"Desmume' in line:
                        identifier = line.strip().split()[0]
                        if re.fullmatch(r'0x[0-9A-Fa-f]+', identifier):
                            window = identifier
                            break
                if window:
                    break
                time.sleep(.5)
            if not window:
                raise RuntimeError('DeSmuME did not display a game window')
            time.sleep(6)
            for name in ('startup', 'settled'):
                if proc.poll() is not None:
                    raise RuntimeError('DeSmuME exited during private screen capture')
                subprocess.run(['xwd', '-id', window, '-silent',
                                '-out', str(out / (name + '.xwd'))],
                               check=True, timeout=10)
                if name == 'startup':
                    time.sleep(10)
            return out / 'startup.xwd', out / 'settled.xwd'
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    print('C348 private DeSmuME frames:', capture(a.rom, a.output))
