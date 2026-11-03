#!/usr/bin/env python3
"""C346: source-provenanced private 3DS GUI C5 inventory, not a bitmap decoder.

Never imply recovered GUI texture containers equal the original two DS screen
frames. This tool emits only sanitized metadata, no original game payloads.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile

MAX_C5 = 12 * 1024 * 1024
EXPECTED = ('gui_title', 'gui_common', 'en/gui_title',
            *(f'en/gui{i:02d}' for i in range(1, 7)),
            'jp/gui_title', *(f'jp/gui{i:02d}' for i in range(1, 7)))


def inventory(archive: Path) -> dict:
    """Validate exact CCI GUI sources and deterministic source-only provenance."""
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        names = [x.filename for x in entries]
        if len(names) != len(set(names)):
            raise ValueError('duplicate source archive names')
        for info in entries:
            name = info.filename
            parts = name.rstrip('/').split('/')
            if (not name or name.startswith('/') or '\\' in name or
                any(x in ('.', '..', '') for x in parts) or
                ((info.external_attr >> 16) & 0o170000) == 0o120000):
                raise ValueError('unsafe source archive path')
        report = []
        for base in EXPECTED:
            src, decoded = f'romfs/gui/{base}.z5', f'decoded_c5/gui/{base}.c5'
            if src not in names or decoded not in names:
                raise ValueError(f'missing matched original/decoded C5 source: {base}')
            srcinfo, info = z.getinfo(src), z.getinfo(decoded)
            if not 0 < srcinfo.file_size <= MAX_C5 or not 0 < info.file_size <= MAX_C5:
                raise ValueError(f'unsafe GUI source size: {base}')
            original = z.read(src)
            raw = z.read(decoded)
            if len(original) != srcinfo.file_size or len(raw) != info.file_size:
                raise ValueError('truncated GUI source')
            if len(raw) < 0x78 or raw[:4] != b'\xc5\x78\x00\x01':
                raise ValueError(f'unsupported original C5 container: {base}')
            offsets = struct.unpack_from('<12I', raw, 0x2c)
            if any(x > len(raw) for x in offsets):
                raise ValueError(f'C5 declared section offset outside container: {base}')
            report.append({
                'original': src, 'original_bytes': len(original),
                'original_sha256': hashlib.sha256(original).hexdigest(),
                'decoded': decoded, 'decoded_bytes': len(raw),
                'decoded_sha256': hashlib.sha256(raw).hexdigest(),
                'c5_version_bytes': raw[:4].hex(),
                'c5_declared_offsets_hex': [f'{x:08x}' for x in offsets],
            })
        return {
            'schema': 'c346-original-gui-source-provenance-v1',
            'source_archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'verified_gui_resource_pairs': len(report),
            'resources': report,
            'actual_texture_pixels_decoded': False,
            'source_measured_home_hotspots': False,
            'original_dual_screen_bitmaps_ready': False,
            'original_release_ready': False,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('refusing to overwrite existing provenance report')
    result = inventory(args.archive)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f'C346 verified {result["verified_gui_resource_pairs"]} original/decoded C5 GUI pairs; DS bitmaps NOT decoded')
