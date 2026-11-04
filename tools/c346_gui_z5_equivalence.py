#!/usr/bin/env python3
"""C346: verify decrypted 3DS GUI Z5 streams against owner-private decoded C5.

GUI Z5 files contain an unwrapped 0x40 compressed stream at byte zero.
This differs from some Pokémon model resources that wrap the stream with a
32-byte header. Emit only hashes and metadata; do not publish C5 contents.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from c346_gui_c5_inventory import inventory, MAX_C5
from native_z5_decoder import decode_stream, DecodeError


def verify(archive: Path) -> dict:
    report = inventory(archive)
    rows = []
    with zipfile.ZipFile(archive) as source:
        for entry in report['resources']:
            name = entry['original']
            raw = source.read(name)
            if not raw or raw[0] != 0x40:
                raise ValueError(f'GUI Z5 stream lacks native 0x40 tag: {name}')
            try:
                decoded = decode_stream(raw, max_output=MAX_C5)
            except DecodeError as exc:
                raise ValueError(f'GUI Z5 decompression failed for {name}') from exc
            actual = source.read(entry['decoded'])
            if decoded != actual:
                raise ValueError(f'GUI Z5 / C5 byte mismatch: {name}')
            digest = hashlib.sha256(decoded).hexdigest()
            if digest != entry['decoded_sha256']:
                raise ValueError(f'GUI C5 provenance digest mismatch: {name}')
            rows.append({'path': name, 'decoded_bytes': len(decoded),
                         'decoded_sha256': digest, 'byte_identical': True})
    return {
        'schema': 'c346-gui-native-z5-equivalence-v1',
        'source_archive_sha256': report['source_archive_sha256'],
        'original_gui_pairs_verified': len(rows),
        'verified': rows,
        'gui_z5_stream_offset': 0,
        'original_ui_texture_conversion_complete': False,
        'source_measured_touch_mapping_complete': False,
        'original_game_release_ready': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('refusing to overwrite a previous verification report')
    result = verify(args.archive)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Verified {result['original_gui_pairs_verified']} original GUI Z5/C5 byte-identical pairs")


if __name__ == '__main__':
    main()
