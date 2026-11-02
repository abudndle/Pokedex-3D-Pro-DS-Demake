#!/usr/bin/env python3
"""C273: compile and unpack an isolated synthetic C272 private diagnostic ROM.

This test uses generated triangle bytes ONLY. It does not use or publish any
Nintendo assets, private reports, or the resulting temporary diagnostic ROM.
Run inside the existing BlocksDS CI container after an asset-free native build.
"""
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tests'))
sys.path.insert(0, str(REPO / 'tools'))
from test_c272_private_rom_build import fixture
from c272_private_rom_build import prepare, build
from verify_nds_rom import verify


def run():
    blocksds = Path(os.environ.get('BLOCKSDS', '/opt/blocksds/core'))
    ndstool = blocksds / 'tools/ndstool/ndstool'
    if not ndstool.is_file() or not os.access(ndstool, os.X_OK):
        raise RuntimeError('C273 requires the real BlocksDS ndstool')
    with tempfile.TemporaryDirectory(prefix='c273-', dir='/tmp') as directory:
        root = Path(directory)
        os.chmod(root, 0o700)
        stage = fixture(root)
        expected = {
            p.relative_to(stage).as_posix(): p.read_bytes()
            for p in (stage / 'geometry').iterdir()
        }
        expected['models/species_map.p3sm'] = (stage / 'models/species_map.p3sm').read_bytes()
        output = root / 'private_output'
        nitro = prepare(stage, output)
        rom = build(nitro, output)
        if verify(rom):
            raise AssertionError('C273 synthetic native ROM has invalid ARM9/ARM7 sections')
        if not rom.is_file() or not rom.stat().st_size:
            raise AssertionError('C273 native ROM was not built')
        manifest = (output / 'C272_PRIVATE_BUILD_SHA256.txt').read_text('ascii')
        digest = hashlib.sha256(rom.read_bytes()).hexdigest()
        if manifest != f'{digest}  C272_PRIVATE_DIAGNOSTIC.nds\\n':
            raise AssertionError('C273 private ROM SHA-256 record mismatch')
        if stat.S_IMODE(rom.stat().st_mode) != 0o600:
            raise AssertionError('C273 private ROM permissions are not restricted')
        extracted = root / 'unpacked'
        extracted.mkdir(mode=0o700)
        process = subprocess.run(
            [str(ndstool), '-x', str(rom), '-d', str(extracted)],
            capture_output=True, text=True, timeout=60, check=False,
        )
        if process.returncode:
            raise AssertionError('C273 real ndstool NitroFS extraction failed: ' +
                                 process.stderr[-1000:])
        found = {
            p.relative_to(extracted).as_posix(): p.read_bytes()
            for p in extracted.rglob('*') if p.is_file()
        }
        if found != expected:
            raise AssertionError('C273 unpacked NitroFS does not exactly match ' +
                                 'the three synthetic runtime files')
        if any('report' in name.lower() or 'sha256' in name.lower()
               for name in found):
            raise AssertionError('C273 leaked private report into NitroFS')
        print('C273 PASS: real BlocksDS compile, ARM9/ARM7 ROM header, '
              'ndstool extraction, exact synthetic NitroFS bytes and private SHA')
        print('C273 evidence: SYNTHETIC ONLY; no original model, emulator, '
              'hardware or visual-fidelity proof')


if __name__ == '__main__':
    run()
