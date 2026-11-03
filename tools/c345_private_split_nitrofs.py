#!/usr/bin/env python3
"""C345: verify owner-private multipart archives and reconstruct in isolated output.

Never publish outputs, use in public CI, or confuse source completeness with release fidelity.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import zipfile

ARCHIVES = ('Pokedex_DS_Private_C141_C148_Asset_Stage.zip',
            'Pokedex_3D_Pro_CCI_Original_UI_Title_AR_Private_Recovery.zip')


def safe_file(path, limit):
    if path.is_symlink() or not path.is_file():
        raise ValueError('missing or symlink private file: '+path.name)
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
        raise ValueError('invalid size/type: '+path.name)
    return info.st_size


def check_zip(path):
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        if len(members) > 20000:
            raise ValueError('too many ZIP entries')
        names, total = set(), 0
        for item in members:
            name = item.filename
            chunks = name.rstrip('/').split('/')
            if (not name or name.startswith('/') or '\\' in name or
                name in names or any(c in ('', '.', '..') for c in chunks) or
                ((item.external_attr >> 16) & 0o170000) == 0o120000):
                raise ValueError('unsafe/duplicate ZIP path')
            names.add(name)
            total += item.file_size
            if total > 1024 * 1024 * 1024:
                raise ValueError('oversized ZIP extraction')
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        return names


def reconstruct(parts_dir, output):
    parts_dir = Path(parts_dir).resolve(strict=True)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or parts_dir in output.parents:
        raise ValueError('output already exists or is under private input directory')
    safe_file(parts_dir / 'manifest.json', 1024 * 1024)
    manifest = json.loads((parts_dir / 'manifest.json').read_text(encoding='utf-8'))
    entries = manifest.get('files')
    if (not isinstance(entries, list) or len(entries) != 2 or
        {item.get('filename') for item in entries} != set(ARCHIVES)):
        raise ValueError('manifest must list both known archives exactly once')
    if not output.parent.is_dir():
        raise ValueError('private output parent does not exist')
    with tempfile.TemporaryDirectory(prefix='.c345-', dir=output.parent) as staging:
        staging = Path(staging)
        result = {}
        for item in entries:
            name = item['filename']
            descriptors = item.get('parts')
            if not isinstance(descriptors, list) or not descriptors:
                raise ValueError('no parts declared')
            full_hash = hashlib.sha256()
            total = 0
            archive = staging / name
            with archive.open('xb') as dest:
                for idx, part in enumerate(descriptors, 1):
                    partname = f'{name}.part{idx:03d}'
                    if (part.get('name') != partname or type(part.get('size')) is not int or
                        not 0 < part['size'] <= 100 * 1024 * 1024):
                        raise ValueError('invalid part definition')
                    source = parts_dir / partname
                    if safe_file(source, 100 * 1024 * 1024) != part['size']:
                        raise ValueError('part size mismatch: '+partname)
                    piece_hash = hashlib.sha256()
                    with source.open('rb') as f:
                        for block in iter(lambda: f.read(1024 * 1024), b''):
                            dest.write(block)
                            piece_hash.update(block)
                            full_hash.update(block)
                            total += len(block)
                    if piece_hash.hexdigest() != part.get('sha256'):
                        raise ValueError('part SHA256 mismatch: '+partname)
            if total != item.get('size') or full_hash.hexdigest() != item.get('sha256'):
                raise ValueError('reassembled archive digest mismatch')
            names = check_zip(archive)
            if name == ARCHIVES[0]:
                counts = {folder:sum(n.startswith(folder+'/') and not n.endswith('/')
                                     for n in names) for folder in ('preview','skeleton','textures')}
                if counts != {'preview':730,'skeleton':730,'textures':4039}:
                    raise ValueError('unexpected model/skeleton/texture roster')
            elif not any(n.endswith('gui_title.z5') for n in names):
                raise ValueError('original title source absent')
            result[name] = {'sha256':full_hash.hexdigest(),'bytes':total,'entries':len(names)}
        (staging/'verification.json').write_text(json.dumps({
            'development_assets_verified':True,
            'original_release_ready':False,
            'original_gui_conversion_complete':False,
            'archives':result},indent=2)+'\n',encoding='utf-8')
        os.rename(staging,output)
        return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    print(json.dumps(reconstruct(a.parts,a.output),indent=2))
