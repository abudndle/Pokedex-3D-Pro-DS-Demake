#!/usr/bin/env python3
"""C360: audit source GUIs' raw C5 UV words against original atlas dimensions.

C359 records source u16 texture coordinates, C352 records the source atlas.
An observed full-atlas (0..2048) mapping and title quad size provide strong
independent evidence for u16 / 2048 as the normalized UV candidate. Preserve
original numbers and exact rational atlas-pixel positions; this alone DOES NOT
verify the runtime sampler, coordinate origin, geometry projection, draw order,
touch rectangles, or composed release frames.

Input original-derived manifests and generated report must stay in PRIVATE Git.
The public project contains only this code and synthetic regression tests.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

DENOMINATOR = 2048
MAX_CATALOG_BYTES = 8_000_000
MAX_GUI = 32
MAX_TEXTURES = 256
MAX_DRAWS = 128
MAX_VERTICES = 10000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def exact(value, dimension):
    numerator = value * dimension
    divisor = math.gcd(numerator, DENOMINATOR)
    return {'numerator': numerator // divisor, 'denominator': DENOMINATOR // divisor}


def read_catalog(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_CATALOG_BYTES:
        raise ValueError('invalid or oversized private source catalog')
    raw = path.read_bytes()
    return json.loads(raw), sha(raw)


def link_atlas_uv(topology, atlases):
    if (not isinstance(topology, dict) or not isinstance(atlases, dict) or
            topology.get('source_archive_sha256') != atlases.get('private_source_archive_sha256') or
            not isinstance(topology.get('resources'), dict) or
            not isinstance(atlases.get('entries'), list)):
        raise ValueError('mismatched source CCI provenance or malformed C352/C359 inputs')
    if not 1 <= len(topology['resources']) <= MAX_GUI or not 1 <= len(atlases['entries']) <= MAX_TEXTURES:
        raise ValueError('C5 source GUI or texture roster outside safety bounds')
    atlas_map = {}
    for e in atlases['entries']:
        if not isinstance(e, dict):
            raise ValueError('invalid original atlas entry')
        path, name = e.get('original_source'), e.get('name')
        width, height = e.get('width'), e.get('height')
        if (not isinstance(path, str) or not path.startswith('decoded_c5/gui/') or
                not path.endswith('.c5') or
                not isinstance(name, str) or not name.isidentifier() or
                type(width) is not int or type(height) is not int or
                width < 8 or height < 8 or width > 1024 or height > 1024 or
                (width & (width-1)) or (height & (height-1))):
            raise ValueError('invalid atlas identity or source dimensions')
        key = (path[len('decoded_c5/gui/'):-3], name)
        if key in atlas_map:
            raise ValueError('duplicate source C5 texture-name mapping')
        atlas_map[key] = e
    result = {}
    count_uv = count_color = count_textured = count_untextured = 0
    full_atlas_quads = []
    for resource_name, source in sorted(topology['resources'].items()):
        if (not isinstance(resource_name, str) or '/' in resource_name and
                resource_name.split('/')[0] not in ('en','jp') or
                not isinstance(source, dict) or not isinstance(source.get('draws'), list) or
                not 1 <= len(source['draws']) <= MAX_DRAWS):
            raise ValueError('invalid original source GUI catalog entry')
        if any(key[0] == resource_name and e['original_c5_sha256'] != source['source_c5_sha256']
               for key, e in atlas_map.items()):
            raise ValueError('C352 original C5 source hash does not match C359 geometry')
        draws = []
        for slot, draw in enumerate(source['draws']):
            if (not isinstance(draw, dict) or draw.get('draw_slot') != slot or
                    not isinstance(draw.get('vertices'), list) or
                    not 3 <= len(draw['vertices']) <= MAX_VERTICES):
                raise ValueError('invalid original GUI draw/vertex sequence')
            name = draw.get('source_texture_name')
            tag = draw.get('vertex_attribute_source_tag')
            if name is None:
                if tag != '7520' or any('original_unsigned_uv_words' in v or
                        len(v.get('original_vertex_color_bytes', [])) != 4
                        for v in draw['vertices']):
                    raise ValueError('untextured GUI vertex records cannot be treated as UVs')
                count_color += len(draw['vertices'])
                count_untextured += 1
                draws.append({'draw_slot': slot, 'source_texture_name': None,
                              'color_vertices': len(draw['vertices']),
                              'source_uv_mapping_available': False})
                continue
            entry = atlas_map.get((resource_name, name))
            if entry is None or tag != '4420':
                raise ValueError('source textured draw has no matching original texture')
            raw_uv = []
            rational_vertices = []
            for v in draw['vertices']:
                pair = v.get('original_unsigned_uv_words')
                if (not isinstance(pair, list) or len(pair) != 2 or
                        any(type(x) is not int or x < 0 or x > DENOMINATOR
                            for x in pair)):
                    raise ValueError('invalid original u16 UV coordinates or fractional span')
                u, vv = pair
                raw_uv.append((u, vv))
                rational_vertices.append({
                    'source_vertex_index': v.get('index'),
                    'source_raw_uv_words': pair,
                    'candidate_atlas_x_pixels_exact': exact(u, entry['width']),
                    'candidate_atlas_y_pixels_exact': exact(vv, entry['height']),
                    'orientation_and_sampler_implementation_verified': False,
                })
            us, vs = zip(*raw_uv)
            corners = {(0,0), (DENOMINATOR,0), (DENOMINATOR,DENOMINATOR), (0,DENOMINATOR)}
            full = len(raw_uv) == 4 and set(raw_uv) == corners
            if full:
                full_atlas_quads.append({'resource': resource_name, 'draw_slot': slot,
                                         'texture_name': name})
            count_uv += len(raw_uv)
            count_textured += 1
            draws.append({
                'draw_slot': slot,
                'scene_node_index': draw['scene_node_index'],
                'source_texture_name': name,
                'atlas_width': entry['width'], 'atlas_height': entry['height'],
                'atlas_png_path': entry['png_path'],
                'atlas_source_png_sha256': entry['png_sha256'],
                'original_uv_minmax_words': [min(us), max(us), min(vs), max(vs)],
                'candidate_atlas_pixel_rect_exact': {
                    'left': exact(min(us), entry['width']),
                    'top': exact(min(vs), entry['height']),
                    'right': exact(max(us), entry['width']),
                    'bottom': exact(max(vs), entry['height']),
                },
                'source_UV_fully_covers_atlas': full,
                'source_uv_sampling_origin_verified': False,
                'source_geometry_projected_to_DS_screen': False,
                'vertices': rational_vertices,
            })
        result[resource_name] = {'draws': draws, 'draw_count': len(draws),
                                 'source_c5_sha256': source['source_c5_sha256']}
    if len({name for (name, _) in atlas_map}) != len(result) or any(
            key[0] not in result for key in atlas_map):
        raise ValueError('C352 atlas source resource roster does not equal C359 geometry')
    sample = result.get('en/gui_title', {}).get('draws', [])
    title_match = False
    if len(sample) > 1 and sample[1].get('source_texture_name') == 'titlepro_en':
        rect = sample[1]['candidate_atlas_pixel_rect_exact']
        title_match = (rect['right'] == {'numerator': 180, 'denominator': 1} and
                       rect['left'] == {'numerator': 0, 'denominator': 1} and
                       rect['top'] == {'numerator': 164, 'denominator': 1} and
                       rect['bottom'] == {'numerator': 256, 'denominator': 1})
    return {
        'schema': 'c360-original-gui-uv-source-atlas-rational-coordinates-v1',
        'source_archive_sha256': topology['source_archive_sha256'],
        'source_gui_resources': len(result),
        'source_atlas_entries': len(atlas_map),
        'source_draws_with_atlas': count_textured,
        'source_draws_without_atlas': count_untextured,
        'source_raw_uv_vertex_records': count_uv,
        'source_color_vertex_records': count_color,
        'source_full_atlas_2048_corner_quads': len(full_atlas_quads),
        'source_full_atlas_2048_quads': full_atlas_quads,
        'observed_uv_denominator_candidate': DENOMINATOR,
        'english_title_180x92_source_pixel_rect_match': title_match,
        'original_unsigned_uv_words_outside_candidate_range': 0,
        'raw_u16_UV_fields_from_source_verified': True,
        'GPU_runtime_UV_normalization_and_origin_verified': False,
        'actual_source_draw_order_and_blend_mode_verified': False,
        'original_title_and_home_projection_verified': False,
        'original_touchscreen_regions_verified': False,
        'original_release_files_still_missing': 16,
        'release_ready': False,
        'resources': result,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--topology', type=Path, required=True)
    p.add_argument('--atlas-manifest', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.report.is_symlink() or args.report.exists() or not args.report.parent.is_dir():
        raise SystemExit('refusing private source report overwrite or missing directory')
    topology, topology_sha = read_catalog(args.topology)
    atlas, atlas_sha = read_catalog(args.atlas_manifest)
    report = link_atlas_uv(topology, atlas)
    report['source_C359_private_topology_report_sha256'] = topology_sha
    report['source_C352_private_atlas_manifest_sha256'] = atlas_sha
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: report[k] for k in (
        'source_gui_resources', 'source_draws_with_atlas',
        'source_raw_uv_vertex_records', 'source_full_atlas_2048_corner_quads',
        'english_title_180x92_source_pixel_rect_match',
        'GPU_runtime_UV_normalization_and_origin_verified', 'release_ready')},
        indent=2))


if __name__ == '__main__':
    main()
