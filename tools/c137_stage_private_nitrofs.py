#!/usr/bin/env python3
"""Safely stage a private original-derived NitroFS QA pack for a BlocksDS build.

This is a development-only path, never a release readiness assertion. Existing
staging directories are never overwritten. No private art is uploaded to GitHub.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

from c137_private_nitrofs_preflight import audit, _scan_zip


def stage(archive_path, output_dir, *, full_crc=True):
    archive_path = Path(archive_path)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError('private staging target already exists; never overwrite files')
    result = audit(archive_path, full_crc=full_crc)
    if not result['native_preview_ready']:
        raise ValueError('private NitroFS model/UV/texture preflight failed')
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='c137-nitrofs-', dir=output_dir.parent) as temp:
        root = Path(temp)
        with zipfile.ZipFile(archive_path) as z:
            names, _ = _scan_zip(z)
            for item in z.infolist():
                if item.is_dir():
                    continue
                target = root / item.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as source, target.open('xb') as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
            extracted = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
            if extracted != {n for n in names if not n.endswith('/')}:
                raise ValueError('NitroFS extraction inventory mismatch')
        # Same-parent rename: no partially staged directory is visible.
        if output_dir.exists():
            raise ValueError('staging target appeared during private unpack')
        os.rename(root, output_dir)
    return {'stage': str(output_dir),
            'files_staged': result['zip_entries'],
            'native_preview_ready': True,
            'original_release_ready': result['original_release_ready'],
            'source_archive_sha256': result['archive_sha256']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--dest',type=Path,required=True)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=stage(args.input,args.dest)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()