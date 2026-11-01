#!/usr/bin/env python3
"""Recover exact C5 node parent hierarchies, source affine transform bytes.

All source data remains private: optionally emit a P3SK v1 skeleton NitroFS
ZIP with original 56-byte per-node records and only the required original
string-table prefix. The public repo contains source and synthetic tests only.
The source hierarchy is proven, but mesh skin weighting and clip playback
remain separate unresolved original 3DS features.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import struct
import zipfile
import zlib
from pathlib import Path
from c140_c5_shader_inventory import ROSTER,PART_RANGES,reference_rows
from c143_c5_channel_groups import CHANNEL_CODES
from c147_c5_named_nodes import resolve_string

MODEL_NAME=re.compile(r'decoded_c5/p([0-9]{3})\.c5\Z')
NODE_BYTES=56
MAX_NODES=256
MAX_C5_BYTES=16*1024*1024
SKELETON_HEADER=struct.Struct('<4sHHHHII')


def inspect_source_nodes(raw:bytes, *, detailed=False):
    if len(raw)<0x78 or raw[:2]!=b'\xc5\x78':
        raise ValueError('not a recovered C5 source')
    n=struct.unpack_from('<I',raw,0x10)[0]>>16
    start=struct.unpack_from('<I',raw,0x38)[0]
    stop=struct.unpack_from('<I',raw,0x3c)[0]
    string_start=struct.unpack_from('<I',raw,0x64)[0]
    if (not 1<=n<=MAX_NODES or start<0x78 or stop>len(raw) or
        stop-start!=n*NODE_BYTES or not 0x78<=string_start<len(raw)):
        raise ValueError('source node table/header count or 56-byte stride mismatch')
    strings_end=string_start
    names=set();string_suffix=0;roots=0;data=[]
    for i in range(n):
        at=start+i*NODE_BYTES
        matrix=struct.unpack_from('<12f',raw,at)
        if not all(math.isfinite(f) for f in matrix):
            raise ValueError('nonfinite source affine transform matrix')
        flags,relative=struct.unpack_from('<II',raw,at+48)
        parent=flags&65535
        kind=flags>>16
        if kind!=1 or (parent!=65535 and parent>=i):
            raise ValueError('invalid original source node kind or parent index')
        if parent==65535:roots+=1
        node_name,suffix=resolve_string(raw,string_start,relative)
        if node_name in names:
            raise ValueError('duplicate original node name')
        names.add(node_name)
        string_suffix+=suffix
        strings_end=max(strings_end,string_start+relative+len(node_name.encode('ascii'))+1)
        data.append({'node_index':i,'original_name_offset':relative,
                     'source_name':node_name,'parent_index':None if parent==65535 else parent,
                     'source_affine_3x4':list(matrix) if detailed else None})
    if not roots:
        raise ValueError('original node forest has no root')
    # C147 source owner low16 is the original node table index. High16
    # is that SAME node's original source string-table relative offset.
    first_track=struct.unpack_from('<I',raw,0x48)[0]
    last_track=struct.unpack_from('<I',raw,0x4c)[0]
    if not (0x78<=first_track<=last_track<=len(raw) and (last_track-first_track)%16==0):
        raise ValueError('C5 animation owner table boundary mismatch')
    attached=[]
    for at in range(first_track,last_track,16):
        pointer,owner,key,code=struct.unpack_from('<4I',raw,at)
        if code!=CHANNEL_CODES[0]:continue
        node_id=owner&65535
        name_offset=owner>>16
        if node_id>=n or data[node_id]['original_name_offset']!=name_offset:
            raise ValueError('original source animation owner does not map to the node table')
        attached.append(node_id)
    if len(attached)!=len(set(attached)):
        raise ValueError('duplicate original source animated node')
    return {'source_nodes':n,'root_nodes':roots,'parent_edges':n-roots,
            'animated_nodes':len(attached),'source_string_suffix_names':string_suffix,
            'source_node_name_mapping_verified':True,
            'original_parent_node_hierarchy_verified':True,
            'source_affine_float_matrix_bits_preserved':True,
            'source_skeletal_skin_weights_verified':False,
            'source_action_clip_semantics_verified':False,
            'source_node_table_bytes':raw[start:stop],
            'source_string_table_prefix':raw[string_start:strings_end],
            **({'original_source_nodes':data} if detailed else {}),
    }


def packed_skeleton(model_id:int,info:dict)->bytes:
    records=info['source_node_table_bytes']
    names=info['source_string_table_prefix']
    if len(records)!=info['source_nodes']*NODE_BYTES or not names:
        raise ValueError('truncated private skeleton source')
    content=records+names
    header=SKELETON_HEADER.pack(b'P3SK',1,model_id,
                                info['source_nodes'],info['root_nodes'],
                                len(names),zlib.crc32(content)&0xffffffff)
    return header+content


def audit(parts,decoder_bundle,c147_summary,*,private_zip=None,detailed_model=None):
    if len(parts)!=3:raise ValueError('three ordered C56 source archives required')
    refs=reference_rows(decoder_bundle)
    prior=json.loads(Path(c147_summary).read_text(encoding='utf-8'))
    if prior.get('original_C56_models_verified')!=730 or set(prior.get('models',{}))!=set(refs):
        raise ValueError('missing original C147 source names report')
    if detailed_model is not None and not re.fullmatch(r'p[0-9]{3}',detailed_model):
        raise ValueError('invalid selected private model label')
    if private_zip is not None and Path(private_zip).exists():
        raise ValueError('will not overwrite private source skeleton archive')
    models={};sums={'nodes':0,'roots':0,'edges':0,'animated':0,'suffix':0};max_nodes=0
    # Reproducible private archives are atomic: never leave a partial ZIP
    # at the requested final location on validation failure.
    temp=None
    if private_zip is not None:
        dst=Path(private_zip)
        dst.parent.mkdir(parents=True,exist_ok=True)
        temp=dst.with_suffix(dst.suffix+'.partial')
        if temp.exists():raise ValueError('partial private source skeleton archive already exists')
    try:
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) if temp is not None else _NoArchive() as out:
            for partnum,path in enumerate(parts):
                lo,hi=PART_RANGES[partnum]
                with zipfile.ZipFile(path) as z:
                    members=z.infolist()
                    if len(members)!=len({e.filename for e in members}):
                        raise ValueError('duplicate source ZIP model entry')
                    for entry in members:
                        m=MODEL_NAME.fullmatch(entry.filename)
                        if not m:raise ValueError('unrecognized source C5 archive member')
                        idx=int(m.group(1));label=f'p{idx:03d}'
                        if idx not in ROSTER or not lo<=idx<=hi or label in models or not 0x78<=entry.file_size<=MAX_C5_BYTES:
                            raise ValueError('displaced or invalid original model')
                        raw=z.read(entry);digest=hashlib.sha256(raw).hexdigest()
                        if (digest!=refs[label]['sha256'] or len(raw)!=int(refs[label]['decoded_bytes']) or
                            digest!=prior['models'][label]['source_sha256']):
                            raise ValueError('original C56/C147 model SHA mismatch: '+label)
                        node=inspect_source_nodes(raw,detailed=(detailed_model==label))
                        if node['animated_nodes']!=prior['models'][label]['original_named_transform_track_groups']:
                            raise ValueError('source original bone/name track count mismatch: '+label)
                        for key,source in (('nodes','source_nodes'),('roots','root_nodes'),
                                           ('edges','parent_edges'),('animated','animated_nodes'),
                                           ('suffix','source_string_suffix_names')):
                            sums[key]+=node[source]
                        max_nodes=max(max_nodes,node['source_nodes'])
                        if temp is not None:
                            out.writestr(f'skeleton/{label}.p3sk',packed_skeleton(idx,node))
                        models[label]={
                            'source_sha256':digest,'original_nodes':node['source_nodes'],
                            'source_parent_edges':node['parent_edges'],
                            'original_animated_nodes':node['animated_nodes'],
                            'original_roots':node['root_nodes'],
                            'source_name_suffix_refs':node['source_string_suffix_names'],
                            **({'nodes':node['original_source_nodes']} if label==detailed_model else {}),
                        }
            if set(models)!=set(refs) or sums['animated']!=prior['source_C5_named_node_tracks_verified']:
                raise ValueError('original C56 skeleton/animation roster incomplete')
        if temp is not None:
            temp.replace(Path(private_zip))
    except BaseException:
        if temp is not None:
            temp.unlink(missing_ok=True)
        raise
    return {'source_models_verified':len(models),
            'original_node_records_verified':sums['nodes'],
            'source_root_nodes':sums['roots'],
            'source_parent_edges_verified':sums['edges'],
            'original_animated_nodes_linked_to_skeleton':sums['animated'],
            'source_interned_node_name_suffix_references':sums['suffix'],
            'max_nodes_in_one_model':max_nodes,
            'private_skeleton_sidecar_files':len(models) if temp is not None else 0,
            'source_parent_hierarchy_verified':True,
            'source_mesh_skin_weights_verified':False,
            'original_animation_clip_bindings_verified':False,
            'DS_skeletal_animation_playback_verified':False,
            'scope':'Original 56-byte C5 node matrices/parent indices/names and animation node links; mesh weights and playing animation NOT validated.',
            'models':dict(sorted(models.items()))}

class _NoArchive:
    def __enter__(self):return None
    def __exit__(self,*args):return False


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts',nargs=3,type=Path,required=True)
    p.add_argument('--decoder-bundle',type=Path,required=True)
    p.add_argument('--c147-summary',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--private-skeleton-zip',type=Path,help='owner-private P3SK v1 ZIP for later native DS rig loader')
    p.add_argument('--detailed-model')
    args=p.parse_args()
    if args.report.exists():p.error('refusing to overwrite an existing private report')
    report=audit(args.parts,args.decoder_bundle,args.c147_summary,
                 private_zip=args.private_skeleton_zip,detailed_model=args.detailed_model)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='models'},indent=2))
if __name__=='__main__':main()