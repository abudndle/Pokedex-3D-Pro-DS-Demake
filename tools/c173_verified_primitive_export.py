"""Export independently verified C5 primitives into native-budgeted P3IX.

The manifest must be independently source-proven. No C5 data may be published.
"""
import argparse
import json
import os
import struct
import zipfile
from pathlib import Path
from c172_primitive_coverage_gate import verify_coverage

MAGIC = b'P3IX'
VERSION = 1
MAX_MESHES = 64
MAX_TRIANGLES = 1800
MAX_SOURCE_BYTES = 64 * 1024 * 1024


def export(manifest, source):
    verify_coverage(manifest, source)
    model = int(manifest['model'][1:])
    rows = sorted(manifest['meshes'], key=lambda row: row['mesh'])
    if not 1 <= len(rows) <= MAX_MESHES:
        raise ValueError('native mesh count exceeded')
    total = 0
    output = bytearray(struct.pack('<4sHHH', MAGIC, VERSION, model, len(rows)))
    for row in rows:
        mesh, triangles = row['mesh'], row['triangles']
        if not 0 <= mesh < MAX_MESHES:
            raise ValueError('native mesh ID exceeded')
        if len(triangles) > MAX_TRIANGLES - total:
            raise ValueError('native triangle budget exceeded')
        total += len(triangles)
        output += struct.pack('<HI', mesh, len(triangles))
        for triangle in triangles:
            if any(index > 65535 for index in triangle):
                raise ValueError('DS u16 vertex index limit exceeded')
            output += struct.pack('<3H', *triangle)
    return bytes(output)


def main():
    from c207_private_c5_xyz import private_path, read_bounded
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_manifest', type=Path)
    parser.add_argument('private_c5_archive', type=Path)
    parser.add_argument('private_output', type=Path)
    args = parser.parse_args()
    manifest_path, archive, output = map(private_path,
        (args.private_manifest, args.private_c5_archive, args.private_output))
    if manifest_path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('oversized private manifest')
    manifest = json.loads(read_bounded(manifest_path))
    with zipfile.ZipFile(archive) as z:
        entry = 'decoded_c5/' + manifest['model'] + '.c5'
        info = z.getinfo(entry)
        if info.file_size > MAX_SOURCE_BYTES:
            raise ValueError('oversized private C5 entry')
        with z.open(info) as stream:
            source = stream.read(MAX_SOURCE_BYTES + 1)
        if len(source) > MAX_SOURCE_BYTES:
            raise ValueError('oversized decompressed C5')
    result = export(manifest, source)
    if not output.parent.is_dir():
        raise ValueError('private output directory missing')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(output, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(result)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    print(json.dumps({'bytes': len(result), 'model': manifest['model'],
                      'verified_meshes': len(manifest['meshes']),
                      'full_original_model_verified': False}))


if __name__ == '__main__':
    main()
