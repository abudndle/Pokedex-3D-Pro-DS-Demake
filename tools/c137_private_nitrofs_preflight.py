#!/usr/bin/env python3
"""C137: independently check private NitroFS readiness against DS native formats.

This source-only checker examines privately held ZIPs without extracting assets,
showing two separate gates: native geometry preview compatibility and original
3DS game release completeness. No commercial asset data belongs in GitHub.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import zipfile

ROSTER = {n for n in range(734) if n not in (721, 722, 723, 724)}
UI_PAGES = ('home','dex','search','moves','types','favorites',
            'challenge','settings','album','ar','records')
DS3M = re.compile(r'preview/p([0-9]{3})\.ds3m\Z')
P3UV = re.compile(r'preview/p([0-9]{3})\.p3uv\Z')
P3PX = re.compile(r'textures/p([0-9]{3})/t([0-9]{3})\.p3px\Z')
MAX_ZIP_CONTENT = 1024 * 1024 * 1024
MAX_INDIVIDUAL = 32 * 1024 * 1024


def _scan_zip(archive):
    infos = archive.infolist()
    names = [x.filename for x in infos]
    if len(set(names)) != len(names):
        raise ValueError('duplicate source NitroFS paths')
    total = 0
    for item in infos:
        name = item.filename
        if (not name or name.startswith('/') or '\\' in name or
            any(part in ('', '.', '..') for part in name.split('/'))):
            raise ValueError('unsafe NitroFS path')
        if (item.flag_bits & 1 or item.file_size > MAX_INDIVIDUAL or
            item.file_size < 0 or stat.S_ISLNK(item.external_attr >> 16)):
            raise ValueError('encrypted or oversized NitroFS entry')
        total += item.file_size
        if total > MAX_ZIP_CONTENT:
            raise ValueError('NitroFS uncompressed size exceeds audit budget')
    return set(names), total


def _model_header(data):
    if len(data) < 16:
        raise ValueError('truncated DS3M')
    magic, version, triangles, reserved, source_triangles = struct.unpack_from('<4sHHII', data)
    if (magic != b'DS3M' or version not in (1, 2) or
        not 1 <= triangles <= 600 or reserved != 0 or
        not triangles <= source_triangles <= 0x7fffffff or
        len(data) != 16 + triangles * (18 if version == 1 else 21)):
        raise ValueError('DS3M disagrees with native previewStreamLoad')
    return triangles


def _uv_header(data, triangles):
    if len(data) != 8 + triangles * 12 or len(data) < 8:
        raise ValueError('P3UV triangle/length mismatch')
    magic, version, n = struct.unpack_from('<4sHH', data)
    if magic != b'P3UV' or version != 1 or n != triangles:
        raise ValueError('P3UV triangle/format mismatch')
    values = struct.unpack_from('<' + 'h' * (6 * n), data, 8)
    if not all(0 <= coord <= 4096 for coord in values):
        raise ValueError('P3UV outside safe unit range')


def _texture_header(z, name):
    with z.open(name) as stream:
        h = stream.read(10)
    if len(h) != 10 or h[:4] != b'P3PX':
        raise ValueError('malformed native P3PX header')
    _, version, width, height = struct.unpack('<4sHHH', h)
    expected = 10 + 2 * width * height
    if (version not in (1, 2) or width not in (8,16,32,64,128,256,512,1024)
        or height not in (8,16,32,64,128,256,512,1024)
        or expected != z.getinfo(name).file_size):
        raise ValueError('native P3PX dimension/byte count invalid')


def audit(path, *, full_crc=False):
    issues = []
    with zipfile.ZipFile(path) as z:
        names, size = _scan_zip(z)
        if full_crc:
            bad = z.testzip()
            if bad:
                raise ValueError('CRC mismatch in private NitroFS archive')
        previews = {}
        for name in names:
            match = DS3M.fullmatch(name)
            if not match:
                continue
            model = int(match.group(1))
            if model not in ROSTER:
                issues.append(f'unexpected source model {model}')
                continue
            try:
                previews[model] = _model_header(z.read(name))
            except ValueError as exc:
                issues.append(f'{name}: {exc}')
        missing_models = sorted(ROSTER - previews.keys())
        for number in missing_models:
            issues.append(f'missing native DS3M preview p{number:03d}')
        uv_count = 0
        for name in names:
            match = P3UV.fullmatch(name)
            if not match:
                continue
            model = int(match.group(1))
            if model not in previews:
                issues.append(f'orphan P3UV companion {name}')
                continue
            try:
                _uv_header(z.read(name), previews[model])
                uv_count += 1
            except ValueError as exc:
                issues.append(f'{name}: {exc}')
        texture_names = [name for name in names if P3PX.fullmatch(name)]
        for name in texture_names:
            try:
                _texture_header(z, name)
            except ValueError as exc:
                issues.append(f'{name}: {exc}')
        # Verify source-derived catalog, Dex, and Move Dex header contracts.
        if 'data/dex_en.p3dx' in names:
            b = z.read('data/dex_en.p3dx')
            if len(b) != 8 + 649*256 or b[:8] != struct.pack('<4sHH', b'P3DX',1,649):
                issues.append('original English Pokédex payload malformed')
        if 'moves.p3dm' in names:
            with z.open('moves.p3dm') as f:
                head = f.read(8)
            if head != struct.pack('<4sHH',b'P3DM',1,559):
                issues.append('original Move Dex header malformed')
        # The release gate is separate: source previews alone cannot satisfy
        # source-exact upper/lower artwork or C5 materials, animations, audio.
        release_missing = []
        for screen in (0,1):
            for index, page in enumerate(UI_PAGES):
                key = f'ui/pages/t{screen}_{index:02d}_{page}.rgb555'
                if key not in names:
                    release_missing.append(key)
                elif z.getinfo(key).file_size != 256*192*2:
                    issues.append(f'{key}: incorrect DS screen bitmap size')
            title = f'ui/title/t{screen}_title.rgb555'
            if title not in names:
                release_missing.append(title)
        for key in ('ui/home_hotspots.p3hm',
                    'ui/pages/t1_01_dex_overlay.rgb555',
                    'data/dex_en.p3dx', 'moves.p3dm'):
            if key not in names:
                release_missing.append(key)
        required = {
            'source_material_ranges': 'materials/p%03d.p3mr',
            'source_shader_capabilities': 'materials/p%03d.p3sc',
            'source_shader_words': 'materials/p%03d.p3sw',
            'mesh_material_bindings': 'materials/p%03d.p3mt',
            'texture_manifests': 'materials/p%03d.p3tx',
            'source_catalogs': 'catalogs/p%03d.p3tm',
        }
        sidecar_counts = {key: sum(pattern % i in names for i in ROSTER)
                          for key,pattern in required.items()}
        missing_sidecars = {key: 730-n for key,n in sidecar_counts.items()}
        preview_ready = not issues and len(previews) == len(ROSTER)
        unverified_release_features = [
            'source-exact texture sampler roles and shader operation words',
            'original Pokemon animations and cries',
            'original music and interface sound effects',
            'original UI touch geometry, upper-screen artwork and 3DS visual parity',
            'all original Challenge modes and remaining gameplay parity',
            'asset-integrated DS and DSi emulator and hardware playthrough',
        ]
        # Do not mark a commercial source-asset port release-ready based solely
        # on structural checks: these requirements are not yet verified.
        ready_for_original_release = False
        digest=hashlib.sha256()
        with Path(path).open('rb') as raw_file:
            for block in iter(lambda: raw_file.read(1024 * 1024), b''):
                digest.update(block)
        return {
            'private_archive_file': Path(path).name,
            'archive_sha256': digest.hexdigest(),
            'zip_entries': len(names), 'uncompressed_bytes': size,
            'native_preview_count': len(previews), 'native_preview_ready': preview_ready,
            'unit_uv_pairs_accepted': uv_count,
            'texture_payload_count': len(texture_names),
            'source_sidecars_present': sidecar_counts,
            'source_sidecars_missing': missing_sidecars,
            'missing_release_ui_and_text': sorted(release_missing),
            'original_release_ready': ready_for_original_release,
            'unverified_release_features': unverified_release_features,
            'asset_integrated_emulator_verified': False,
            'issues': sorted(issues),
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--crc-all',action='store_true')
    p.add_argument('--require-preview-ready',action='store_true')
    p.add_argument('--require-release-ready',action='store_true')
    args=p.parse_args()
    result=audit(args.input,full_crc=args.crc_all)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'missing_release_ui_and_text'},indent=2))
    if args.require_preview_ready and not result['native_preview_ready']:
        raise SystemExit(1)
    if args.require_release_ready and not result['original_release_ready']:
        raise SystemExit(1)


if __name__=='__main__':
    main()