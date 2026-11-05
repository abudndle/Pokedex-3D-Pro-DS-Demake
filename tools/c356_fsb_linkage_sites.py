#!/usr/bin/env python3
"""C356: source-exact 3DS FSB opaque linkage table audit.

Each FSB linkage has a 12-byte (key_a,key_b,code_site) record. The opaque
keys are stable between original English/Japanese scripts. Their meanings,
actual UI instruction operands, coordinates and touch geometry are UNKNOWN.
Original-derived output is private-only. Public CI uses synthetic data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile

from c355_fsb_ui_symbols import parse_fsb, MAX_FSB

FSB_DIRS = ('romfs/scripts/', 'romfs/scripts_en/')
RECORD_BYTES = 12
MAX_LINKAGES = 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def linkage_record_table(data, stem):
    parsed = parse_fsb(data, stem)
    _, code_end, linkage_end, string_start, final_size, *_ = struct.unpack_from('<8I', data)
    if not 32 < code_end < linkage_end == string_start < final_size:
        raise ValueError('invalid FSB compiled/linkage section bounds')
    length = linkage_end - code_end
    if length % RECORD_BYTES or not RECORD_BYTES <= length <= MAX_LINKAGES * RECORD_BYTES:
        raise ValueError('FSB linkage table must contain bounded 12-byte records')
    entries, site_set = [], set()
    for i, pos in enumerate(range(code_end, linkage_end, RECORD_BYTES)):
        key_a, key_b, site = struct.unpack_from('<III', data, pos)
        if not 32 <= site < code_end:
            raise ValueError('FSB linkage site outside compiled bytecode')
        if site in site_set:
            raise ValueError('duplicate FSB linkage patch site')
        site_set.add(site)
        lo, hi = max(32, site - 8), min(code_end, site + 8)
        entries.append({
            'index': i, 'record_offset': pos,
            'linkage_key_a': f'{key_a:08x}', 'linkage_key_b': f'{key_b:08x}',
            'code_site_offset': site, 'compiled_relative_offset': site - 32,
            'code_window_start': lo, 'code_window_end': hi,
            'code_window_sha256': digest(data[lo:hi]),
            'semantic_function_resolved': False, 'layout_coordinate_verified': False,
        })
    return {
        'source_bytes': len(data), 'source_sha256': digest(data),
        'compiled_bytecode_sha256': parsed['compiled_section']['sha256'],
        'linkage_section_start': code_end, 'linkage_section_end': linkage_end,
        'linkage_section_sha256': digest(data[code_end:linkage_end]),
        'source_linkages': entries, 'linkages': len(entries),
    }

def recover(archive):
    archive = Path(archive)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('missing or symlinked source archive')
    result = {}
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        names = [i.filename for i in members]
        if len(set(names)) != len(names):
            raise ValueError('ambiguous duplicate CCI source ZIP entries')
        for item in members:
            name = item.filename
            if (not name or name.startswith('/') or '\\' in name or
                    any(x in ('', '.', '..') for x in name.rstrip('/').split('/')) or
                    stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError('unsafe original CCI ZIP path')
        scripts = sorted(n for n in names if n.endswith('.fsb') and n.startswith(FSB_DIRS))
        if len(scripts) != 50:
            raise ValueError('expected exactly 50 JP/EN original FSB sources')
        for path in scripts:
            info = z.getinfo(path)
            if not 128 <= info.file_size <= MAX_FSB:
                raise ValueError('oversized original FSB script')
            raw = z.read(path)
            if len(raw) != info.file_size:
                raise ValueError('truncated original FSB source')
            result[path] = linkage_record_table(raw, Path(path).stem)
    pairs = []
    for en in sorted(n for n in result if n.startswith(FSB_DIRS[1])):
        jp = FSB_DIRS[0] + en[len(FSB_DIRS[1]):]
        if jp not in result:
            raise ValueError('missing matching original JP FSB script')
        jp_rows, en_rows = result[jp]['source_linkages'], result[en]['source_linkages']
        jp_keys = [(x['linkage_key_a'], x['linkage_key_b']) for x in jp_rows]
        en_keys = [(x['linkage_key_a'], x['linkage_key_b']) for x in en_rows]
        if jp_keys != en_keys:
            raise ValueError('JP/EN original script linkage identities differ')
        pairs.append({
            'script_stem': Path(en).stem, 'english_source': en,
            'japanese_source': jp, 'linkages_each': len(en_rows),
            'ordered_opaque_keys_equal': True,
            'identical_compiled_code_site_offsets':
                [x['code_site_offset'] for x in jp_rows] ==
                [x['code_site_offset'] for x in en_rows],
            'function_names_verified': False,
        })
    if len(pairs) != 25:
        raise ValueError('expected 25 original JP/EN linkage pairs')
    totals = {scope: sum(row['linkages'] for name, row in result.items()
                         if name.startswith(scope)) for scope in FSB_DIRS}
    if totals[FSB_DIRS[0]] != totals[FSB_DIRS[1]]:
        raise ValueError('original language linkage counts differ')
    return {
        'schema': 'c356-original-fsb-opaque-linkage-bytecode-sites-v1',
        'source_archive_sha256': digest(archive.read_bytes()),
        'original_scripts_verified': len(result), 'paired_language_scripts': len(pairs),
        'original_linkage_records': sum(totals.values()),
        'original_linkages_per_language': {'jp': totals[FSB_DIRS[0]],
                                            'en': totals[FSB_DIRS[1]]},
        'paired_linkage_identifiers_all_equal': True,
        'relocations_with_invalid_code_sites': 0,
        'record_format': '12-byte little-endian (opaque u32 key A, opaque u32 key B, u32 compiled-code site offset)',
        'verified_runtime_function_mappings': 0,
        'original_ui_coordinates_decoded': False,
        'original_touchscreen_geometry_decoded': False,
        'original_title_and_menu_screen_composition_complete': False,
        'original_missing_release_targets_remaining': 16,
        'release_ready': False,
        'script_entries': result, 'language_pairs': pairs,
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        raise SystemExit('private report must not overwrite an existing path')
    report = recover(args.archive)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: report[k] for k in (
        'original_scripts_verified', 'paired_language_scripts',
        'original_linkage_records', 'original_linkages_per_language',
        'original_ui_coordinates_decoded', 'release_ready')}, indent=2))

if __name__ == '__main__':
    main()
