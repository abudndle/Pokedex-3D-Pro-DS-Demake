#!/usr/bin/env python3
"""C249: privately stage native geometry for explicitly assigned QA Dex slots.

All species bindings here are DIAGNOSTIC, not recovered 3DS mappings. C179
native GL acceptance proves transport only. Keep source sidecars, SHA reports,
NitroFS and resulting ROM outside the public repository and CI artifacts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import tempfile

from c211_private_source_pair import validate_native_pair, MAX_VX_BYTES, MAX_IX_BYTES
from c183_private_geometry_batch import build_probe, outside_repo

MAX_MAPPING_BYTES = 128 * 1024
MAX_ASSIGNMENTS = 649
ROSTER = frozenset(i for i in range(734) if i not in (721, 722, 723, 724))


def private_path(path, *, directory=False):
    """Reject symlinked ancestors and paths inside this public source tree."""
    candidate = Path(path).expanduser().absolute()
    if any(p.is_symlink() for p in (candidate, *candidate.parents)):
        raise ValueError('private path symlink rejected')
    resolved = outside_repo(candidate)
    if directory and (not resolved.is_dir() or not stat.S_ISDIR(resolved.stat().st_mode)):
        raise ValueError('private input directory missing')
    return resolved


def read_regular(path, limit):
    path = private_path(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= limit:
            raise ValueError('private input not a bounded single-link regular file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) != info.st_size:
            raise ValueError('private input changed during bounded read')
        return data
    finally:
        os.close(fd)


def parse_assignments(data):
    try:
        doc = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError('invalid private diagnostic mapping JSON') from exc
    if (type(doc) is not dict or set(doc) != {'purpose', 'assignments'}
            or doc['purpose'] != 'diagnostic' or type(doc['assignments']) is not list
            or not 1 <= len(doc['assignments']) <= MAX_ASSIGNMENTS):
        raise ValueError('explicit diagnostic assignments required; source mapping not inferred')
    species_seen = set()
    assignments = []
    for item in doc['assignments']:
        if (type(item) is not dict or set(item) != {'species', 'model'}
                or type(item['species']) is not int or not 1 <= item['species'] <= 649
                or type(item['model']) is not int or item['model'] not in ROSTER):
            raise ValueError('invalid explicit diagnostic species/model identity')
        if item['species'] in species_seen:
            raise ValueError('duplicate diagnostic species slot')
        species_seen.add(item['species'])
        assignments.append((item['species'], item['model']))
    return assignments


def write_private_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def stage(source_dir, mapping_json, destination):
    source_dir = private_path(source_dir, directory=True)
    mapping_json = private_path(mapping_json)
    destination = private_path(destination)
    if destination.exists() or not destination.parent.is_dir():
        raise ValueError('private destination must not exist and parent must exist')
    if destination == source_dir or source_dir in destination.parents:
        raise ValueError('destination must not be inside source directory')
    assignments = parse_assignments(read_regular(mapping_json, MAX_MAPPING_BYTES))
    models = sorted({model for _, model in assignments})
    stage_dir = Path(tempfile.mkdtemp(prefix='.c249-', dir=destination.parent))
    os.chmod(stage_dir, 0o700)
    try:
        geometry = stage_dir / 'geometry'
        geometry.mkdir(mode=0o700)
        models_dir = stage_dir / 'models'
        models_dir.mkdir(mode=0o700)
        report = {'schema': 'p3d-c249-private-diagnostic-nitrofs-v1',
                  'diagnostic_species_assignments_only': True,
                  'original_species_resource_mapping_verified': False,
                  'original_renderer_vertex_material_skinning_verified': False,
                  'asset_integrated_emulator_verified': False,
                  'original_game_release_ready': False,
                  'species_slots': len(assignments), 'unique_models': len(models),
                  'models': {}}
        map_values = [0xffff] * 649
        for species, model in assignments:
            map_values[species - 1] = model
        write_private_file(models_dir / 'species_map.p3sm',
                           struct.pack('<4sHH649H', b'P3SM', 1, 649, *map_values))
        def check_model(model, executable):
            name = f'p{model:03d}'
            vertex_path = source_dir / (name + '.p3vx')
            index_path = source_dir / (name + '.p3ix')
            vx = read_regular(vertex_path, MAX_VX_BYTES)
            ix = read_regular(index_path, MAX_IX_BYTES)
            result = validate_native_pair(vx, ix, model)
            if executable is not None:
                run = subprocess.run([str(executable), str(vertex_path), str(index_path),
                                      str(model), str(result['triangles'])],
                                     capture_output=True, timeout=15, check=False)
                if run.returncode:
                    raise ValueError('native C179 GL probe rejected geometry pair')
            write_private_file(geometry / (name + '.p3vx'), vx)
            write_private_file(geometry / (name + '.p3ix'), ix)
            report['models'][name] = {'vertices': result['vertices'],
                                     'triangles': result['triangles'],
                                     'native_gl_probe_passed': executable is not None,
                                     'p3vx_sha256': hashlib.sha256(vx).hexdigest(),
                                     'p3ix_sha256': hashlib.sha256(ix).hexdigest()}
        with tempfile.TemporaryDirectory(prefix='c249-native-probe-') as tmp:
            executable = Path(tmp) / 'c179-probe'
            build_probe(executable)
            for model in models:
                check_model(model, executable)
        write_private_file(stage_dir / 'C249_PRIVATE_DIAGNOSTIC_REPORT.json',
                           (json.dumps(report, indent=2, sort_keys=True) + '\n').encode())
        for directory in (geometry, models_dir, stage_dir):
            fd = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        if destination.exists() or destination.is_symlink():
            raise ValueError('private destination appeared during staging')
        os.rename(stage_dir, destination)
        parent_fd = os.open(destination.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return report
    finally:
        if stage_dir.exists():
            shutil.rmtree(stage_dir)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-dir', required=True, type=Path)
    ap.add_argument('--mapping-json', required=True, type=Path)
    ap.add_argument('--destination', required=True, type=Path)
    args = ap.parse_args()
    result = stage(args.source_dir, args.mapping_json, args.destination)
    print(json.dumps({'diagnostic_species_slots': result['species_slots'],
                      'native_pairs_staged': result['unique_models'],
                      'original_species_mapping_verified': False,
                      'private_asset_emulator_verified': False}, sort_keys=True))


if __name__ == '__main__':
    main()
