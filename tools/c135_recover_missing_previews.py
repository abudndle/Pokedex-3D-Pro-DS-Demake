#!/usr/bin/env python3
"""C135: recover four source-derived DS3M previews from private C56 C5 models.

C7's unique C5 geometry extractor is the source of face and vertex data. This
converter samples original faces, never invents shapes, UVs, or material roles.
C135 output is a PRIVATE preview-only NitroFS overlay, not a release ROM.
"""
import argparse
import csv
import io
import hashlib
import json
import math
import re
import struct
import zipfile
from pathlib import Path

MISSING = (730, 731, 732, 733)
NEUTRAL_RGB = bytes((192, 224, 232))
MAX_TRIANGLES = 600


def _sample_quotas(groups, limit):
    lengths = [len(group) for group in groups]
    if not lengths or len(lengths) > limit or any(n < 1 for n in lengths):
        raise ValueError('invalid source mesh-group coverage')
    target = min(sum(lengths), limit)
    quotas = [1] * len(lengths)
    while sum(quotas) < target:
        candidates = [j for j, n in enumerate(lengths) if quotas[j] < n]
        if not candidates:
            raise ValueError('source sampling quota stalled')
        selected = max(candidates, key=lambda j: (lengths[j] / quotas[j], -j))
        quotas[selected] += 1
    return quotas


def build_ds3m_v2(vertices, groups, limit=MAX_TRIANGLES):
    """Use source vertex/triangle groups; no use of proprietary test fixtures."""
    if not 1 <= limit <= MAX_TRIANGLES or len(vertices) != len(groups):
        raise ValueError('bad DS model triangle budget or group count')
    if not vertices or not groups or len(groups) > limit:
        raise ValueError('missing source mesh groups')
    total_vertices, total_faces = 0, 0
    lower = [float('inf')] * 3
    upper = [float('-inf')] * 3
    for xyz, faces in zip(vertices, groups):
        if not len(xyz) or not len(faces):
            raise ValueError('empty source mesh')
        total_vertices += len(xyz)
        total_faces += len(faces)
        for v in xyz:
            if len(v) != 3 or not all(math.isfinite(float(x)) for x in v):
                raise ValueError('nonfinite source vertex')
            if any(abs(float(x)) > 100 for x in v):
                raise ValueError('implausible source vertex')
            for axis in range(3):
                lower[axis] = min(lower[axis], float(v[axis]))
                upper[axis] = max(upper[axis], float(v[axis]))
    extent = max(upper[i] - lower[i] for i in range(3))
    if not 0.00001 < extent < 100:
        raise ValueError('implausible original model dimensions')
    center = [(upper[i] + lower[i]) * 0.5 for i in range(3)]
    factor = (1.8 / extent) * 4096.0
    positions = []
    quotas = _sample_quotas(groups, limit)
    for xyz, faces, take in zip(vertices, groups, quotas):
        for k in range(take):
            face = faces[((2 * k + 1) * len(faces)) // (2 * take)]
            if len(face) != 3:
                raise ValueError('non-triangular source face')
            indices = [int(i) for i in face]
            if len(set(indices)) != 3 or any(i < 0 or i >= len(xyz) for i in indices):
                raise ValueError('invalid source face indices')
            a, b, c = (xyz[i] for i in indices)
            ab = [float(b[i] - a[i]) for i in range(3)]
            ac = [float(c[i] - a[i]) for i in range(3)]
            cross = (ab[1]*ac[2]-ab[2]*ac[1],
                     ab[2]*ac[0]-ab[0]*ac[2],
                     ab[0]*ac[1]-ab[1]*ac[0])
            if sum(v*v for v in cross) <= 1e-18:
                raise ValueError('zero-area source preview face')
            for i in indices:
                for axis in range(3):
                    fixed = round((float(xyz[i][axis]) - center[axis]) * factor)
                    if not -32768 <= fixed <= 32767:
                        raise ValueError('source vertex cannot fit DS 4.12')
                    positions.append(fixed)
    n = len(positions) // 9
    if not 1 <= n <= limit or len(positions) != n * 9:
        raise ValueError('sampled DS3M topology invalid')
    blob = struct.pack('<4sHHII', b'DS3M', 2, n, total_vertices, total_faces)
    blob += struct.pack('<' + 'h' * len(positions), *positions)
    blob += NEUTRAL_RGB * n
    if len(blob) != 16 + n * 21:
        raise AssertionError('DS3M v2 length mismatch')
    return blob, {'source_vertices': total_vertices, 'source_triangles': total_faces,
                  'source_mesh_groups': len(groups), 'preview_triangles': n,
                  'source_meshes_sampled': len(quotas),
                  'preview_sha256': hashlib.sha256(blob).hexdigest(),
                  'uv_verified': False, 'materials_verified': False}


def _validate_c86_missing(report_path):
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    rows = report.get('per_model')
    if not isinstance(rows, list) or len(rows) != 730:
        raise ValueError('C86 preview inventory must contain 730 models')
    missing = {row.get('model_id') for row in rows if row.get('fallback_preview') is False}
    if missing != {f'p{i:03d}' for i in MISSING}:
        raise ValueError('C86 original missing model list has changed')


def read_c56_reference(bundle):
    with zipfile.ZipFile(bundle) as z:
        with z.open('C56_validation.csv') as handle:
            raw = handle.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('C56 source validation CSV over size limit')
    entries = {}
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        label = row.get('model', '')
        if not re.fullmatch(r'p[0-9]{3}', label) or label in entries:
            raise ValueError('duplicate/invalid C56 source validation ID')
        if not re.fullmatch(r'[0-9a-f]{64}', row.get('sha256', '')):
            raise ValueError('missing C56 source integrity hash')
        entries[label] = row
    if len(entries) != 730:
        raise ValueError('incomplete original C56 source validation inventory')
    return entries


def recover_patch(c56_part3, decoder_bundle, c86_report, private_patch, private_report):
    # Import heavy research dependencies only for private source conversion;
    # synthetic public tests can check the portable DS3M writer without NumPy.
    from c135_c5_geometry import recover
    _validate_c86_missing(c86_report)
    reference = read_c56_reference(decoder_bundle)
    rows = []
    with zipfile.ZipFile(c56_part3) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate C56 model archive entries')
        with zipfile.ZipFile(private_patch, 'w', compression=zipfile.ZIP_DEFLATED) as out:
            for i in MISSING:
                label = f'p{i:03d}'
                c5name = f'decoded_c5/{label}.c5'
                info = source.getinfo(c5name)
                if not 0 < info.file_size <= 16 * 1024 * 1024:
                    raise ValueError('private C5 model exceeds bounded input size')
                data = source.read(info)
                expected = reference[label]
                if (len(data) != int(expected['decoded_bytes']) or
                    hashlib.sha256(data).hexdigest() != expected['sha256'] or
                    expected['status'] != 'strict_valid'):
                    raise ValueError(f'{label} C56 source hash/size mismatch')
                solutions = recover(data)
                if len(solutions) != 1:
                    raise ValueError(f'{label} ambiguous C5 geometry recovery')
                vstart, vertices, mesh_ranges, areas = solutions[0]
                if not vstart or len(vertices) != len(mesh_ranges) or any(a <= 1e-9 for a in areas):
                    raise ValueError(f'{label} C5 geometry bounds or face area invalid')
                blob, stats = build_ds3m_v2(vertices, [g[1] for g in mesh_ranges])
                out.writestr(f'preview/{label}.ds3m', blob)
                rows.append({'model_id': label, 'c56_sha256': expected['sha256'],
                             'source_vertex_start': hex(vstart), **stats})
            out.writestr('C135_PRIVATE_README.txt',
                         'C135 privately recovered source-derived DS3M v2 model previews for p730-p733.\n'
                         'Source C5 triangles are sampled without invented geometry.\n'
                         'NEUTRAL colors only. UV/material/shader mapping is NOT restored.\n'
                         'Not a finished original 3DS render and not for public GitHub.\n')
    report = {'source_models_recovered': 4, 'preview_models_recovered': 4,
              'private_only': True, 'full_original_rendering_verified': False,
              'models': rows}
    Path(private_report).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def combine_private_nitrofs(base, patch, output):
    """Add four missing previews to a private C86 NitroFS ZIP atomically."""
    with zipfile.ZipFile(base) as original, zipfile.ZipFile(patch) as recovered:
        names = original.namelist()
        additions = {f'preview/p{i:03d}.ds3m' for i in MISSING}
        if len(names) != len(set(names)) or (set(names) & additions):
            raise ValueError('C86 archive names duplicated or model already present')
        existing = {n for n in names if re.fullmatch(r'preview/p[0-9]{3}\.ds3m', n)}
        if len(existing) != 726:
            raise ValueError('C86 baseline is not the 726-preview private bundle')
        if set(recovered.namelist()) != additions | {'C135_PRIVATE_README.txt'}:
            raise ValueError('unexpected C135 private overlay member')
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=5) as merged:
            for entry in original.infolist():
                merged.writestr(entry.filename, original.read(entry))
            for name in sorted(recovered.namelist()):
                merged.writestr(name, recovered.read(name))
    with zipfile.ZipFile(output) as check:
        if check.testzip() is not None:
            raise ValueError('combined private NitroFS CRC failure')
        names = check.namelist()
        if len(names) != len(set(names)) or len([n for n in names if re.fullmatch(r'preview/p[0-9]{3}\.ds3m', n)]) != 730:
            raise ValueError('combined private NitroFS missing original preview entries')
    return {'combined_archive': Path(output).name, 'preview_models': 730,
            'sha256': hashlib.sha256(Path(output).read_bytes()).hexdigest(),
            'original_material_bindings_verified': False, 'release_ready': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c56-part3', type=Path, required=True)
    parser.add_argument('--decoder-bundle', type=Path, required=True)
    parser.add_argument('--c86-report', type=Path, required=True)
    parser.add_argument('--patch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--base-nitrofs', type=Path)
    parser.add_argument('--combined-out', type=Path)
    args = parser.parse_args()
    if bool(args.base_nitrofs) != bool(args.combined_out):
        parser.error('--base-nitrofs and --combined-out must be supplied together')
    report = recover_patch(args.c56_part3, args.decoder_bundle, args.c86_report,
                           args.patch, args.report)
    if args.base_nitrofs:
        report['private_combined'] = combine_private_nitrofs(args.base_nitrofs, args.patch,
                                                              args.combined_out)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()