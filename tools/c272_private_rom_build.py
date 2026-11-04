#!/usr/bin/env python3
"""C272: isolated private diagnostic NitroFS ROM build, never a public release.

Consumes a C249 diagnostic stage outside the checkout. Revalidates native
geometry, P3SM and SHA report, then copies ONLY runtime files to a clean
private NitroFS tree. C249 reports/hashes are deliberately not packed into ROM.
No emulator or original-rendering claim is made by a successful build.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys

from c211_private_source_pair import validate_native_pair, MAX_VX_BYTES, MAX_IX_BYTES
from c183_private_geometry_batch import outside_repo

REPO = Path(__file__).resolve().parents[1]
REPORT = 'C249_PRIVATE_DIAGNOSTIC_REPORT.json'
MAP_BYTES = 8 + 649 * 2
MAX_REPORT_BYTES = 256 * 1024


def private_path(path):
    p = Path(path).expanduser().absolute()
    if any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('private symlink path rejected')
    return outside_repo(p)


def read_private(path, limit):
    path = private_path(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or not 0 < st.st_size <= limit:
            raise ValueError('unsafe or oversized private regular file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) != st.st_size:
            raise ValueError('private input changed during read')
        return data
    finally:
        os.close(fd)


def _write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _names(directory):
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError('private NitroFS directory missing or unsafe')
    return {p.name for p in directory.iterdir()}


def validate_stage(stage):
    stage = private_path(stage)
    if _names(stage) != {'geometry', 'models', REPORT}:
        raise ValueError('unexpected C249 stage root entries')
    if _names(stage / 'models') != {'species_map.p3sm'}:
        raise ValueError('unexpected C249 model entries')
    report = json.loads(read_private(stage / REPORT, MAX_REPORT_BYTES))
    if (type(report) is not dict or report.get('schema') != 'p3d-c249-private-diagnostic-nitrofs-v1'
            or report.get('diagnostic_species_assignments_only') is not True
            or report.get('original_species_resource_mapping_verified') is not False
            or report.get('asset_integrated_emulator_verified') is not False
            or report.get('original_game_release_ready') is not False
            or report.get('original_renderer_vertex_material_skinning_verified') is not False
            or type(report.get('models')) is not dict):
        raise ValueError('invalid diagnostic provenance report')
    mapping = read_private(stage / 'models/species_map.p3sm', MAP_BYTES)
    if len(mapping) != MAP_BYTES or struct.unpack_from('<4sHH', mapping) != (b'P3SM', 1, 649):
        raise ValueError('invalid P3SM species map')
    ids = struct.unpack_from('<649H', mapping, 8)
    used = {model for model in ids if model != 0xffff}
    if (not used or any(model > 733 or 721 <= model <= 724 for model in used)
            or sum(model != 0xffff for model in ids) != report.get('species_slots')
            or len(used) != report.get('unique_models')
            or set(report['models']) != {f'p{model:03d}' for model in used}):
        raise ValueError('P3SM mapping differs from private report')
    expected = {f'p{model:03d}.{ext}' for model in used for ext in ('p3vx', 'p3ix')}
    if _names(stage / 'geometry') != expected:
        raise ValueError('unexpected or missing C249 geometry files')
    payloads = {'models/species_map.p3sm': mapping}
    for model in sorted(used):
        name = f'p{model:03d}'
        vx = read_private(stage / 'geometry' / (name + '.p3vx'), MAX_VX_BYTES)
        ix = read_private(stage / 'geometry' / (name + '.p3ix'), MAX_IX_BYTES)
        info = validate_native_pair(vx, ix, model)
        row = report['models'][name]
        if (type(row) is not dict or row.get('p3vx_sha256') != hashlib.sha256(vx).hexdigest()
                or row.get('p3ix_sha256') != hashlib.sha256(ix).hexdigest()
                or row.get('vertices') != info['vertices']
                or row.get('triangles') != info['triangles']
                or row.get('native_gl_probe_passed') is not True):
            raise ValueError('native pair differs from SHA-backed C249 report')
        payloads[f'geometry/{name}.p3vx'] = vx
        payloads[f'geometry/{name}.p3ix'] = ix
    return payloads


def prepare(stage, output):
    payloads = validate_stage(stage)
    output = private_path(output)
    if output.exists() or not output.parent.is_dir():
        raise ValueError('private output must not exist; parent required')
    output.mkdir(mode=0o700)
    try:
        nitro = output / 'nitrofs'
        nitro.mkdir(mode=0o700)
        for folder in ('geometry', 'models'):
            (nitro / folder).mkdir(mode=0o700)
        for name, data in payloads.items():
            _write(nitro / name, data)
        return nitro
    except BaseException:
        shutil.rmtree(output)
        raise


def build(nitro, output):
    # Makefile.native interpolates NITROFSDIR into shell recipes and find.
    # Reject shell metacharacters and whitespace in private output paths.
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', str(nitro)):
        raise ValueError('unsafe private NitroFS path for native Makefile')
    work = output / 'work'
    work.mkdir(mode=0o700)
    shutil.copytree(REPO / 'source', work / 'source')
    shutil.copy2(REPO / 'Makefile.native', work / 'Makefile.native')
    # Explicit public source dependencies, outside the private NitroFS tree.
    # Never copy unrelated recovery data or reports into the build inputs.
    vendor=work/'third_party'/'pngle'
    vendor.mkdir(parents=True)
    for name in ('pngle.c','pngle.h','miniz.c','miniz.h','LICENSE','README.md'):
        shutil.copy2(REPO/'third_party'/'pngle'/name,vendor/name)
    subprocess.run(['make', '-f', 'Makefile.native', f'NITROFSDIR={nitro}', 'rom'],
                   cwd=work, check=True, timeout=300)
    rom = work / 'Pokedex3D_DS_BlocksDS.nds'
    sys.path.insert(0, str(REPO / 'tools'))
    from verify_nds_rom import verify
    if verify(rom):
        raise ValueError('private ROM ARM9/ARM7 header invalid')
    target = output / 'C272_PRIVATE_DIAGNOSTIC.nds'
    _write(target, read_private(rom, 64 * 1024 * 1024))
    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    _write(output / 'C272_PRIVATE_BUILD_SHA256.txt', (sha + '  C272_PRIVATE_DIAGNOSTIC.nds\n').encode())
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    nitro = prepare(args.stage, args.output)
    if args.preflight_only:
        print('C272 private NitroFS preflight: PASS (no ROM built or emulator run)')
        return 0
    rom = build(nitro, private_path(args.output))
    print(f'C272 PRIVATE ROM built and header validated: {rom}; emulator NOT tested')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
