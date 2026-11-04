#!/usr/bin/env python3
"""C349: drive A/Right/B on a private asset-integrated ROM in DeSmuME.

Only run in a PRIVATE repository runner; captures may contain original art.
Uses the existing tested DeSmuME 0.9.13-only CI SDL remapper so host key events
are not mistaken for an actual DS input response.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c236_desmume_keymap import write_config


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, timeout=20, **kwargs)


def capture(rom, output):
    rom, output = Path(rom).absolute(), Path(output).absolute()
    if rom.is_symlink() or not rom.is_file() or output.exists() or not output.parent.is_dir():
        raise ValueError('ROM or private capture output invalid')
    if not os.environ.get('DISPLAY'):
        raise ValueError('Xvfb DISPLAY required')
    binary = shutil.which('desmume-cli') or '/usr/games/desmume-cli'
    if not Path(binary).is_file():
        raise ValueError('DeSmuME CLI is unavailable')
    version = run(['dpkg-query', '-W', '-f=${Version}', 'desmume'],
                  capture_output=True, text=True).stdout.strip()
    if not version.startswith('0.9.13-'):
        raise ValueError('unsupported DeSmuME keymap ABI ' + version)
    tools = ('cc', 'xwd', 'xwininfo', 'xdotool')
    if any(shutil.which(name) is None for name in tools):
        raise ValueError('missing X11/host compiler input probe dependencies')
    output.mkdir(mode=0o700)
    lib = output / 'c240_test_key_adapter.so'
    source = Path(__file__).resolve().parent / 'c238_sdl_event_trace.c'
    run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fPIC', '-shared',
         str(source), '-ldl', '-o', str(lib)])
    config = output / 'config'
    config.mkdir(mode=0o700)
    write_config(config)
    env = dict(os.environ)
    env.update(XDG_CONFIG_HOME=str(config), LD_PRELOAD=str(lib),
               P3D_C240_ADAPT_0913='1', P3D_C238_TRACE='1')
    with (output / 'emulator.log').open('wb') as log:
        proc = subprocess.Popen([binary, '--disable-sound', str(rom)],
                                env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            window = ''
            for _ in range(40):
                if proc.poll() is not None:
                    raise RuntimeError('private-ROM DeSmuME process exited early')
                tree = run(['xwininfo', '-root', '-tree'],
                           capture_output=True, text=True).stdout
                for line in tree.splitlines():
                    if '"Desmume' in line:
                        candidate = line.strip().split()[0]
                        if re.fullmatch(r'0x[0-9a-fA-F]+', candidate):
                            window = candidate
                            break
                if window:
                    break
                time.sleep(.5)
            if not window:
                raise RuntimeError('no DeSmuME window')
            time.sleep(7)
            run(['xdotool', 'windowfocus', '--sync', window])
            def screenshot(name):
                if proc.poll() is not None:
                    raise RuntimeError('DeSmuME terminated while navigating')
                path = output / (name + '.xwd')
                run(['xwd', '-id', window, '-silent', '-out', str(path)])
                if not path.is_file() or path.stat().st_size < 100:
                    raise RuntimeError('missing private emulator screenshot')
            def press(key):
                run(['xdotool', 'keydown', key])
                time.sleep(.4)
                run(['xdotool', 'keyup', key])
                time.sleep(2.5)
            screenshot('home')
            press('x')  # DS A
            screenshot('dex')
            press('d')  # DS Right (C240 host test adapter)
            screenshot('next_dex')
            press('b')  # DS B (C240 host test adapter)
            screenshot('back')
            return [output / f'{name}.xwd' for name in
                    ('home', 'dex', 'next_dex', 'back')]
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print('C349 private navigation frames:', capture(args.rom, args.output))
