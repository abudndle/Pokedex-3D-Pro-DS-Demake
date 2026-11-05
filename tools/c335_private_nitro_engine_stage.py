#!/usr/bin/env python3
"""C335: private verified original P3VX/P3IX -> official Nitro Engine OBJ2DL.

This does NOT create substitute geometry. The OBJ is an intermediate encoding
of the source-verified original triangle order; obj2dl.py (Nitro Engine) does
the actual DS hardware display-list conversion. No source models, converted
assets, source hashes or private reports belong in public GitHub / CI artifacts.

For animated originals, use the upstream md5_to_dsma converter only AFTER
independent C5 skin/bone mapping verification. 3DS skinning cannot currently
be verified for all Pokémon, so this script deliberately produces static
display lists only; the native optional renderer accepts independently
verified DSM/DSA under the same P3NE binding contract.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from c211_private_source_pair import validate_native_pair
from c207_private_c5_xyz import private_path,read_bounded

MAX_DISPLAY_LIST=262144

def export_obj(vx:bytes,ix:bytes,model:int)->str:
    info=validate_native_pair(vx,ix,model)
    if not info['triangles']:
        raise ValueError('no source triangles')
    meshes={}
    pos=16
    start=0
    result=['# Exact DS4.12 source vertices; no generated faces or UVs.']
    count=struct.unpack_from('<H',vx,8)[0]
    table_end=16+count*8
    vertices_start=table_end
    for _ in range(count):
        mesh,n,offset=struct.unpack_from('<HHI',vx,pos)
        if offset!=start:
            raise ValueError('source vertex table is not contiguous')
        meshes[mesh]=(start,n)
        for i in range(n):
            a,b,c=struct.unpack_from('<3h',vx,vertices_start+(start+i)*6)
            result.append(f'v {a/4096:.9g} {b/4096:.9g} {c/4096:.9g}')
        pos+=8;start+=n
    cursor=10
    index_count=struct.unpack_from('<H',ix,8)[0]
    for _ in range(index_count):
        mesh,triangles=struct.unpack_from('<HI',ix,cursor)
        cursor+=6
        first,n=meshes[mesh]
        result.append(f'g source_mesh_{mesh}')
        for _ in range(triangles):
            a,b,c=struct.unpack_from('<3H',ix,cursor)
            cursor+=6
            if max(a,b,c)>=n:
                raise ValueError('source index escaped its original mesh')
            result.append(f'f {first+a+1} {first+b+1} {first+c+1}')
    return '\n'.join(result)+'\n'

def manifest_bytes(vx:bytes,ix:bytes,model:int,dl:bytes)->bytes:
    validate_native_pair(vx,ix,model)
    if (len(dl)<8 or len(dl)>MAX_DISPLAY_LIST or len(dl)%4!=0
        or struct.unpack_from('<I',dl,0)[0]!=(len(dl)-4)//4):
        raise ValueError('invalid Nitro Engine hardware display list')
    header=struct.pack('<4sBBHIIIIII',b'P3NE',1,1,model,
        zlib.crc32(vx),zlib.crc32(ix),len(dl),zlib.crc32(dl),0,0)
    assert len(header)==32
    return header+struct.pack('<I',zlib.crc32(header))

def check_evidence(evidence:bytes,model:int,info:dict):
    if len(evidence)>2*1024*1024:
        raise ValueError('oversized original-source verification report')
    try:
        report=json.loads(evidence)
    except (ValueError,UnicodeDecodeError) as e:
        raise ValueError('invalid private provenance report') from e
    if (report.get('schema')!='p3d-c245-private-ordered-source-geometry-pair-v1'
       or not report.get('source_c5_face_bytes_exact_unique')
       or not report.get('source_c5_xyz_order_exact')
       or not report.get('native_p3vx_p3ix_pair_valid')
       or report.get('mesh_count')!=info['vertex_meshes']
       or report.get('triangle_count')!=info['triangles']
       or report.get('vertex_count')!=info['vertices']):
        raise ValueError('source C5 topology/position proof is missing or inconsistent')
    # The report verifies the original C5 source order, NOT skin/UV/material
    # fidelity, original runtime loading, 3DS shader semantics, or all species.
    return report

def stage(p3vx:Path,p3ix:Path,evidence:Path,converter:Path,output:Path):
    p3vx,p3ix,evidence,output=map(private_path,(p3vx,p3ix,evidence,output))
    if (not converter.is_file() or converter.name!='obj2dl.py'
        or not output.is_dir() or output.is_symlink()):
        raise ValueError('original Nitro Engine obj2dl.py and private output directory required')
    stem=p3vx.stem
    if (len(stem)!=4 or stem[0]!='p' or not stem[1:].isdigit()
        or p3ix.name!=stem+'.p3ix' or evidence.name!=stem+'.json'):
        raise ValueError('source pair and C245 proof must share the pNNN model identity')
    model=int(stem[1:])
    vx,ix=read_bounded(p3vx),read_bounded(p3ix)
    info=validate_native_pair(vx,ix,model)
    check_evidence(read_bounded(evidence),model,info)
    dst_dl=output/(stem+'.dl')
    dst_manifest=output/(stem+'.p3ne')
    if dst_dl.exists() or dst_manifest.exists() or dst_dl.is_symlink() or dst_manifest.is_symlink():
        raise ValueError('private destination files must not already exist')
    with tempfile.TemporaryDirectory(prefix='.p3d-c335-',dir=output) as temporary:
        tmp=Path(temporary)
        obj=tmp/(stem+'.obj');dl=tmp/(stem+'.dl')
        obj.write_text(export_obj(vx,ix,model),encoding='utf-8')
        os.chmod(obj,0o600)
        subprocess.run([sys.executable,str(converter),'--input',str(obj),
                '--output',str(dl),'--texture','8','8'],
                check=True,timeout=60,capture_output=True,text=True)
        data=read_bounded(dl)
        header=manifest_bytes(vx,ix,model,data)
        manifest=tmp/(stem+'.p3ne')
        manifest.write_bytes(header)
        os.chmod(dl,0o600);os.chmod(manifest,0o600)
        os.rename(dl,dst_dl)
        os.rename(manifest,dst_manifest)
    return {'model':model,'triangles':info['triangles'],
        'converted_using':'Nitro Engine obj2dl.py',
        'has_original_3ds_textures':False,
        'has_original_3ds_animation':False,
        'private_original_render_verified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--p3vx',type=Path,required=True)
    p.add_argument('--p3ix',type=Path,required=True)
    p.add_argument('--c245-report',type=Path,required=True)
    p.add_argument('--obj2dl',type=Path,required=True)
    p.add_argument('--private-nitro-dir',type=Path,required=True)
    a=p.parse_args()
    result=stage(a.p3vx,a.p3ix,a.c245_report,a.obj2dl,a.private_nitro_dir)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    main()
