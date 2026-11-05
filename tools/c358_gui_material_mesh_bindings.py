#!/usr/bin/env python3
"""C358: recover original GUI material -> mesh -> scene-node binding evidence.

Original C5 v2 has 52-byte material, 40-byte mesh/draw, 20-byte
vertex descriptor and 12-byte index descriptor records. Preserve their
source-indexed relationships to C351 original texture names and C357
native scene transforms. DO NOT mistake source-space geometry bounds
or static material reference for original display projection, dynamic
texture animation, UV mapping, rendering, or touch coordinates.

Only code and synthetic tests belong in the public repository.
Original-derived output and exact original records belong in private Git.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
import zipfile

from c351_gui_texture_atlases import descriptors
from c357_gui_scene_transforms import EXPECTED, MAX_C5, parse_scene_transforms

MATERIAL_SIZE = 52
DRAW_SIZE = 40
VERTEX_DESCRIPTOR_SIZE = 20
INDEX_DESCRIPTOR_SIZE = 12


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _section(data, inner, length, start_pointer, end_pointer, record_size,
             maximum=64):
    begin = struct.unpack_from('<I', data, inner + start_pointer)[0]
    end = struct.unpack_from('<I', data, inner + end_pointer)[0]
    if (not 0x78 <= begin < end <= length or
            (end - begin) % record_size or
            not 1 <= (end - begin) // record_size <= maximum):
        raise ValueError(f'invalid original C5 section at {start_pointer:#x}')
    return inner+begin, inner+end


def extract_source_bindings(data):
    scene = parse_scene_transforms(data)
    textures, _ = descriptors(data)
    inner = scene['embedded_c5_offset']
    declared = scene['embedded_declared_bytes']
    materials_begin, materials_end = _section(
        data, inner, declared, 0x34, 0x38, MATERIAL_SIZE)
    nodes = scene['transforms']
    vbegin, vend = _section(
        data, inner, declared, 0x3c, 0x40, VERTEX_DESCRIPTOR_SIZE)
    ibegin, iend = _section(
        data, inner, declared, 0x40, 0x44, INDEX_DESCRIPTOR_SIZE)
    mesh_rel = struct.unpack_from('<I', data, inner+0x44)[0]
    mesh_next = [struct.unpack_from('<I', data, inner+off)[0]
                 for off in (0x48, 0x4c, 0x50, 0x54, 0x64)]
    possible = [end for end in mesh_next if mesh_rel < end <= declared]
    if not possible:
        raise ValueError('missing original mesh record section terminator')
    mesh_end_rel = min(possible)
    if (mesh_rel < 0x78 or (mesh_end_rel-mesh_rel) % DRAW_SIZE or
            not 1 <= (mesh_end_rel-mesh_rel)//DRAW_SIZE <= 64):
        raise ValueError('invalid original C5 mesh draw records')
    mesh_begin, mesh_end = inner+mesh_rel, inner+mesh_end_rel
    material_count = (materials_end-materials_begin)//MATERIAL_SIZE
    draw_count = (mesh_end-mesh_begin)//DRAW_SIZE
    vertex_buffers = (vend-vbegin)//VERTEX_DESCRIPTOR_SIZE
    index_buffers = (iend-ibegin)//INDEX_DESCRIPTOR_SIZE
    declared_materials, declared_nodes = struct.unpack_from('<HH', data, inner+0x10)
    declared_vertex_buffers, declared_index_buffers = struct.unpack_from('<HH', data, inner+0x14)
    if (declared_materials, declared_nodes) != (material_count,len(nodes)):
        raise ValueError('declared C5 node/material counts do not match sections')
    if (declared_vertex_buffers, declared_index_buffers) != (vertex_buffers,index_buffers):
        raise ValueError('declared C5 geometry descriptor counts do not match sections')
    if vertex_buffers != draw_count or index_buffers != draw_count:
        raise ValueError('original GUI draw descriptor count differs from buffers')

    materials = []
    for i in range(material_count):
        pos = materials_begin+i*MATERIAL_SIZE
        record = data[pos:pos+MATERIAL_SIZE]
        texture_index = struct.unpack_from('<H', record, 2)[0]
        if texture_index != 0xffff and texture_index >= len(textures):
            raise ValueError('original material refers to texture outside source C5')
        tex = textures[texture_index] if texture_index != 0xffff else None
        materials.append({
            'index':i, 'original_byte_offset':pos,
            'original_material_record_sha256':sha(record),
            'source_texture_index':None if tex is None else texture_index,
            'source_texture_name':None if tex is None else tex['name'],
            'source_texture_GPU_sha256':None if tex is None else tex['gpu_sha256'],
            'texture_width':None if tex is None else tex['width'],
            'texture_height':None if tex is None else tex['height'],
            'static_source_texture_reference_present':tex is not None,
            'dynamic_material_texture_changes_decoded':False,
        })

    drawings = []
    textured = 0
    for i in range(draw_count):
        pos = mesh_begin+i*DRAW_SIZE
        raw = data[pos:pos+DRAW_SIZE]
        material_id, draw_slot, buffer_slot, node_id = struct.unpack_from('<4H', raw)
        primitive_count = struct.unpack_from('<I', raw, 8)[0]
        geometry_words = struct.unpack_from('<6f', raw, 16)
        if (material_id >= material_count or draw_slot != i or
                buffer_slot != i or node_id >= len(nodes) or
                not 1 <= primitive_count <= 65535):
            raise ValueError('invalid C5 material/draw/buffer/node linkage index')
        if (any(not math.isfinite(value) or abs(value)>1_000_000
                for value in geometry_words) or
                any(geometry_words[a]>geometry_words[a+3] for a in range(3))):
            raise ValueError('invalid C5 source-space draw bounds')
        mat = materials[material_id]
        if mat['static_source_texture_reference_present']:
            textured += 1
        drawings.append({
            'draw_slot':i, 'original_mesh_record_offset':pos,
            'original_mesh_record_sha256':sha(raw),
            'material_index':material_id, 'vertex_descriptor_index':draw_slot,
            'index_descriptor_index':buffer_slot,
            'scene_node_index':node_id,
            'scene_node_transform_source_offset':nodes[node_id]['source_matrix_offset'],
            'scene_node_translation':nodes[node_id]['translation'],
            'primitive_count_source_value':primitive_count,
            'original_bounds_xyz_min':list(geometry_words[:3]),
            'original_bounds_xyz_max':list(geometry_words[3:]),
            'source_texture_index':mat['source_texture_index'],
            'source_texture_name':mat['source_texture_name'],
            'source_texture_GPU_sha256':mat['source_texture_GPU_sha256'],
            'static_texture_binding_evidence':mat['static_source_texture_reference_present'],
            'source_space_bounds_not_projected_DS_pixels':True,
            'texture_UV_or_draw_order_verified':False,
        })
    return {
        'original_c5_sha256':sha(data),
        'original_scene_nodes':len(nodes),
        'original_texture_entries':len(textures),
        'original_material_records':material_count,
        'original_mesh_draw_records':len(drawings),
        'source_textured_draw_records':textured,
        'draw_records_without_static_texture':len(drawings)-textured,
        'material_section_sha256':sha(data[materials_begin:materials_end]),
        'mesh_section_sha256':sha(data[mesh_begin:mesh_end]),
        'vertex_descriptors_section_sha256':sha(data[vbegin:vend]),
        'index_descriptors_section_sha256':sha(data[ibegin:iend]),
        'source_material_section_offset':materials_begin,
        'source_mesh_section_offset':mesh_begin,
        'original_static_material_texture_indices_extracted':True,
        'runtime_material_switches_verified':False,
        'original_texture_UV_coordinates_verified':False,
        'original_scene_projection_verified':False,
        'original_touchscreen_hit_regions_verified':False,
        'materials':materials,
        'draws':drawings,
    }


def recover(archive):
    archive=Path(archive)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('missing original private source ZIP or archive symlink')
    entries={}
    with zipfile.ZipFile(archive) as z:
        listed=z.infolist()
        names=[x.filename for x in listed]
        if len(names)!=len(set(names)):
            raise ValueError('ambiguous original source ZIP duplicate names')
        for entry in listed:
            name=entry.filename
            if (not name or name.startswith('/') or '\\' in name or
                any(part in ('','.','..') for part in name.rstrip('/').split('/')) or
                stat.S_ISLNK(entry.external_attr>>16)):
                raise ValueError('unsafe original private source archive entry')
        for key in EXPECTED:
            path=f'decoded_c5/gui/{key}.c5'
            if path not in names or not 0<z.getinfo(path).file_size<=MAX_C5:
                raise ValueError('missing original GUI C5 source: '+key)
            raw=z.read(path)
            if len(raw)!=z.getinfo(path).file_size:
                raise ValueError('truncated original source C5 input')
            entries[key]=extract_source_bindings(raw)
    for i in range(1,7):
        en=entries[f'en/gui{i:02d}']
        jp=entries[f'jp/gui{i:02d}']
        if (en['material_section_sha256']!=jp['material_section_sha256'] or
            en['mesh_section_sha256']!=jp['mesh_section_sha256']):
            raise ValueError('original English/Japanese numbered GUI material/mesh difference')
    totals={name:sum(entry[name] for entry in entries.values())
        for name in ('original_scene_nodes','original_texture_entries',
                     'original_material_records','original_mesh_draw_records',
                     'source_textured_draw_records','draw_records_without_static_texture')}
    if totals != {'original_scene_nodes':78,'original_texture_entries':132,
                  'original_material_records':35,'original_mesh_draw_records':51,
                  'source_textured_draw_records':45,
                  'draw_records_without_static_texture':6}:
        raise ValueError('original GUI material/mesh/texture roster differs')
    return {
        'schema':'c358-original-gui-structural-material-draw-node-texrefs-v1',
        'source_archive_sha256':sha(archive.read_bytes()),
        'original_C5_resources':len(entries),
        'identical_EN_JP_numbered_material_and_mesh_pairs':6,
        **totals,
        'source_static_atlas_to_draw_links_recovered':True,
        'original_projected_256x192_screen_art_complete':False,
        'original_uv_mapping_and_dynamic_texture_state_complete':False,
        'original_home_touchmap_verified':False,
        'original_release_targets_missing':16,
        'release_ready':False,
        'resources':entries,
    }


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    if a.report.exists() or a.report.is_symlink() or not a.report.parent.is_dir():
        raise SystemExit('refusing to overwrite or write outside an existing private output directory')
    report=recover(a.archive)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in (
        'original_C5_resources','original_scene_nodes','original_texture_entries',
        'original_material_records','original_mesh_draw_records',
        'source_textured_draw_records','draw_records_without_static_texture',
        'release_ready')},indent=2))
