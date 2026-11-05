#!/usr/bin/env python3
"""C359: source-exact original C5 GUI packed vertices and indexed triangles.

The embedded C5 GPU geometry starts exactly 0x78 bytes after the embedded
C5 metadata. Draw descriptors index 16-byte XYZ+tail vertices and 16-bit
triangle indices. Attribute tags 0x4420 and 0x7520 distinguish two observed
4-byte tails. For 0x4420, preserve TWO RAW unsigned texture-coordinate words,
without assuming UV scale/origin. For 0x7520, preserve FOUR RAW color bytes,
without claiming color channel ordering. This is source geometry evidence,
NOT original DS screen pixel projection, runtime draw order, animation or
HOME touchscreen geometry. Original-derived output stays PRIVATE.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zipfile

from c358_gui_material_mesh_bindings import extract_source_bindings
from c357_gui_scene_transforms import EXPECTED, MAX_C5, parse_scene_transforms

VERTEX_SIZE=16
VERTEX_DESCRIPTOR_SIZE=20
INDEX_DESCRIPTOR_SIZE=12
UV_WORDS=0x4420
VERTEX_COLOR=0x7520


def sha(data):
    return hashlib.sha256(data).hexdigest()


def recover_geometry(data):
    binding=extract_source_bindings(data)
    scene=parse_scene_transforms(data)
    inner=scene['embedded_c5_offset']
    body_end=inner+scene['embedded_declared_bytes']
    payload_start=body_end+0x78
    geom_size=struct.unpack_from('<I',data,inner+8)[0]
    texture_gpu_start=0x78+struct.unpack_from('<I',data,4)[0]
    if (geom_size<12 or geom_size>256*1024 or
            payload_start+geom_size>texture_gpu_start):
        raise ValueError('source C5 geometry span outside original metadata')
    geom=data[payload_start:payload_start+geom_size]
    if len(geom)!=geom_size:
        raise ValueError('truncated embedded original geometry payload')
    vstart,vend,istart,iend=struct.unpack_from('<4I',data,inner+0x3c)
    vcount=(vend-vstart)//VERTEX_DESCRIPTOR_SIZE
    icount=(iend-istart)//INDEX_DESCRIPTOR_SIZE
    draws=binding['draws']
    if (vcount!=len(draws) or icount!=len(draws) or
            vstart<0x78 or (vend-vstart)%VERTEX_DESCRIPTOR_SIZE or
            (iend-istart)%INDEX_DESCRIPTOR_SIZE):
        raise ValueError('source geometry descriptor counts mismatch original draws')
    decoded=[]
    total_vertices=total_indices=0
    vertex_cursor=0
    index_cursor=None
    for i,draw in enumerate(draws):
        vpos=inner+vstart+i*VERTEX_DESCRIPTOR_SIZE
        ipos=inner+istart+i*INDEX_DESCRIPTOR_SIZE
        voff,reserved,packed,tail_tag,reserved2=struct.unpack_from('<5I',data,vpos)
        vertex_count=packed&0xffff
        format_tag=packed>>16
        if (reserved or reserved2 or format_tag!=0x0210 or
                tail_tag not in (UV_WORDS,VERTEX_COLOR) or
                not 3<=vertex_count<=4096 or voff!=vertex_cursor):
            raise ValueError('invalid original C5 packed vertex descriptor')
        vertex_bytes=vertex_count*VERTEX_SIZE
        vertex_cursor+=vertex_bytes
        if vertex_cursor>len(geom):
            raise ValueError('C5 vertex descriptor extends beyond GPU geometry')
        ioff,izero,nindices,index_stride=struct.unpack_from('<IIHH',data,ipos)
        if (izero or index_stride!=2 or not 3<=nindices<=65535 or
                nindices%3 or nindices!=draw['primitive_count_source_value']*3):
            raise ValueError('invalid original C5 indexed triangle descriptor')
        if index_cursor is None:
            if ioff!=vertex_cursor and i==len(draws)-1:
                raise ValueError('invalid source vertex/index section boundary')
            index_cursor=ioff
        if ioff!=index_cursor:
            raise ValueError('noncontiguous C5 index buffers')
        index_cursor+=nindices*index_stride
        if index_cursor>len(geom):
            raise ValueError('C5 index descriptor extends beyond GPU geometry')
        blob=geom[voff:voff+vertex_bytes]
        faces_blob=geom[ioff:ioff+nindices*2]
        indices=list(struct.unpack('<'+'H'*nindices,faces_blob))
        if any(x>=vertex_count for x in indices):
            raise ValueError('triangle references vertex outside original source buffer')
        vertices=[]
        for v in range(vertex_count):
            start=v*VERTEX_SIZE
            x,y,z=struct.unpack_from('<3f',blob,start)
            if any(not math.isfinite(coord) or abs(coord)>1e6 for coord in (x,y,z)):
                raise ValueError('invalid source vertex XYZ coordinate')
            vertex={
                'index':v, 'source_byte_offset':payload_start+voff+start,
                'original_record_sha256':sha(blob[start:start+VERTEX_SIZE]),
                'source_xyz':[x,y,z],
                'original_last_four_bytes_hex':blob[start+12:start+16].hex(),
            }
            if tail_tag==UV_WORDS:
                vertex['original_unsigned_uv_words']=list(struct.unpack_from('<2H',blob,start+12))
                vertex['original_uv_scale_origin_verified']=False
            else:
                vertex['original_vertex_color_bytes']=list(blob[start+12:start+16])
                vertex['original_vertex_color_channel_order_verified']=False
            vertices.append(vertex)
        bounds=draw['original_bounds_xyz_min'],draw['original_bounds_xyz_max']
        # Source AABB is observed independent of vertex bytes in the mesh table.
        # Require all INDEXED original vertices to be inside their corresponding
        # independently recovered source geometry bounds.
        for idx in set(indices):
            xyz=vertices[idx]['source_xyz']
            if any(not bounds[0][k]-0.01<=xyz[k]<=bounds[1][k]+0.01 for k in range(3)):
                raise ValueError('original indexed vertex conflicts with source draw AABB')
        decoded.append({
            'draw_slot':i,
            'material_index':draw['material_index'],
            'scene_node_index':draw['scene_node_index'],
            'source_texture_name':draw['source_texture_name'],
            'vertex_descriptor_source_offset':vpos,
            'index_descriptor_source_offset':ipos,
            'vertex_buffer_source_offset':payload_start+voff,
            'index_buffer_source_offset':payload_start+ioff,
            'vertex_attribute_source_tag':f'{tail_tag:04x}',
            'xyz_vertex_count':vertex_count,
            'triangle_indices_count':nindices,
            'indexed_triangle_count':nindices//3,
            'vertex_buffer_sha256':sha(blob),
            'index_buffer_sha256':sha(faces_blob),
            'raw_uv_words_are_not_verified_screen_UVs':True,
            'source_triangle_winding_not_runtime_proven':True,
            'vertices':vertices,
            'triangle_vertex_indices':[indices[j:j+3] for j in range(0,nindices,3)],
        })
        total_vertices+=vertex_count
        total_indices+=nindices
    if vertex_cursor!=decoded[0]['index_buffer_source_offset']-payload_start:
        raise ValueError('original vertex buffers do not terminate at first index buffer')
    if index_cursor!=geom_size or total_vertices*VERTEX_SIZE+total_indices*2!=geom_size:
        raise ValueError('original vertex/index descriptor sizes do not fill C5 geometry')
    if any(i!=draw['draw_slot'] for i,draw in enumerate(draws)):
        raise ValueError('C5 source draw order inconsistency')
    return {
        'source_c5_sha256':sha(data),
        'source_geometry_offset':payload_start,
        'source_geometry_bytes':geom_size,
        'source_geometry_sha256':sha(geom),
        'draw_records':len(decoded),
        'original_vertices':total_vertices,
        'original_triangle_indices':total_indices,
        'original_indexed_triangles':total_indices//3,
        'uv_word_vertex_records':sum(d['xyz_vertex_count'] for d in decoded
                                      if d['vertex_attribute_source_tag']==f'{UV_WORDS:04x}'),
        'color_byte_vertex_records':sum(d['xyz_vertex_count'] for d in decoded
                                         if d['vertex_attribute_source_tag']==f'{VERTEX_COLOR:04x}'),
        'original_static_texture_binding_verified':True,
        'original_uv_coordinate_scale_and_origin_verified':False,
        'source_xyz_to_DS_projection_verified':False,
        'source_draw_order_and_blend_state_verified':False,
        'actual_original_title_home_frames_composed':False,
        'draws':decoded,
    }


def recover(archive):
    archive=Path(archive)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError('missing or symlinked original private C5 ZIP')
    all_rows={}
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):
            raise ValueError('ambiguous duplicate original source ZIP member')
        for key in EXPECTED:
            name=f'decoded_c5/gui/{key}.c5'
            if name not in names or not 0<z.getinfo(name).file_size<=MAX_C5:
                raise ValueError('missing or oversized original GUI source: '+key)
            all_rows[key]=recover_geometry(z.read(name))
    for i in range(1,7):
        a,b=all_rows[f'en/gui{i:02d}'],all_rows[f'jp/gui{i:02d}']
        if a['source_geometry_sha256']!=b['source_geometry_sha256']:
            raise ValueError('English/Japanese original GUI indexed geometry mismatch')
    sums={field:sum(row[field] for row in all_rows.values()) for field in (
        'draw_records','original_vertices','original_triangle_indices',
        'original_indexed_triangles','uv_word_vertex_records','color_byte_vertex_records')}
    if sums!={'draw_records':51,'original_vertices':2352,
             'original_triangle_indices':3864,'original_indexed_triangles':1288,
             'uv_word_vertex_records':1960,'color_byte_vertex_records':392}:
        raise ValueError('source original C5 geometry roster differs')
    return {
        'schema':'c359-original-gui-indexed-vertex-geometry-and-raw-uv-evidence-v1',
        'source_archive_sha256':sha(archive.read_bytes()),
        'original_gui_resources':len(all_rows),
        'identical_numbered_jp_en_geometry_pairs':6,
        **sums,
        'source_exact_vertex_geometry_buffers_recovered':True,
        'normalized_original_uv_mapping_verified':False,
        'actual_original_screen_projection_verified':False,
        'DS_release_title_and_home_frames_composed':False,
        'original_HOME_touch_coordinates_verified':False,
        'required_release_files_missing':16,
        'release_ready':False,
        'resources':all_rows,
    }


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists() or args.report.is_symlink() or not args.report.parent.is_dir():
        raise SystemExit('Refusing overwrite or nonexistent output parent for original source data')
    report=recover(args.archive)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({name:report[name] for name in (
        'original_gui_resources','draw_records','original_vertices',
        'original_triangle_indices','original_indexed_triangles',
        'required_release_files_missing','release_ready')},indent=2))
