#!/usr/bin/env python3
"""Privately stage source-verified C5 track owner-to-P3SK associations (P3TB v1).

Public source code only. Input C5 dumps, output P3TB, and original model
names/transforms are PRIVATE and must never be committed to GitHub.
"""
import argparse
import hashlib
import json
import re
import struct
import tempfile
import os
import zipfile
import zlib
from pathlib import Path

from c140_c5_shader_inventory import ROSTER,PART_RANGES,reference_rows
from c147_c5_named_nodes import inspect_model as inspect_tracks
from c148_c5_skeleton_hierarchy import inspect_source_nodes,packed_skeleton

C5_NAME=re.compile(r'decoded_c5/p([0-9]{3})\.c5\Z')
HEADER=struct.Struct('<4sHHHHII')
RECORD=struct.Struct('<HHI104s')
MAX_SOURCE_BYTES=16*1024*1024

def pack_binding(model_id,raw,private_p3sk):
    """Return source-exact owner association; no guessed action or playback."""
    nodes=inspect_source_nodes(raw,detailed=True)
    tracks=inspect_tracks(raw,detailed=True)['original_source_named_node_tracks']
    if private_p3sk!=packed_skeleton(model_id,nodes):
        raise ValueError('P3SK does not exactly match the source C5 model')
    if len(tracks)!=nodes['animated_nodes'] or len(tracks)>160:
        raise ValueError('source animation owner count does not match original nodes')
    records=[];seen=set();previous=-1
    for track in tracks:
        index=track['source_owner_token']
        offset=track['name_offset_in_original_C5_strings']
        first=track['source_first_track_record']
        name=track['original_node_name']
        if (index in seen or not 0<=index<len(nodes['original_source_nodes']) or
            not 0<=offset<=65535 or not 0<=first<=0xffffffff or first<=previous):
            raise ValueError('duplicate, out-of-range or unsorted original owner')
        node=nodes['original_source_nodes'][index]
        if node['original_name_offset']!=offset or node['source_name']!=name:
            raise ValueError('original C5 owner index/name/offset does not match P3SK')
        label=name.encode('ascii')
        if not 1<=len(label)<=96:
            raise ValueError('invalid original C5 node name')
        records.append(RECORD.pack(index,offset,first,label))
        seen.add(index);previous=first
    if not records:return b''
    payload=b''.join(records)
    return HEADER.pack(b'P3TB',1,model_id,len(records),0,
                       zlib.crc32(private_p3sk[20:]),zlib.crc32(payload))+payload

def audit(parts,decoder_bundle,c147_summary,skeleton_zip,output_zip):
    refs=reference_rows(decoder_bundle)
    prior=json.loads(Path(c147_summary).read_text(encoding='utf-8'))
    roster={f'p{i:03d}' for i in ROSTER}
    if (len(parts)!=3 or set(refs)!=roster or
        prior.get('original_C56_models_verified')!=730 or
        set(prior.get('models',{}))!=roster):
        raise ValueError('original 730-model C56/C147 SHA inventory missing')
    destination=Path(output_zip)
    if destination.exists():
        raise ValueError('refuse to overwrite private track binding package')
    temp=destination.with_suffix(destination.suffix+'.partial')
    if temp.exists():
        raise ValueError('stale private partial output exists')
    destination.parent.mkdir(parents=True,exist_ok=True)
    total=0;models=0;zero=0;verified=set()
    try:
        with zipfile.ZipFile(skeleton_zip) as rigs,zipfile.ZipFile(
                temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
            expected={f'skeleton/{label}.p3sk' for label in roster}
            if set(rigs.namelist())!=expected or len(rigs.namelist())!=len(expected):
                raise ValueError('missing, duplicate or unexpected original P3SK')
            for partnum,path in enumerate(parts):
                low,high=PART_RANGES[partnum]
                with zipfile.ZipFile(path) as source:
                    names=source.namelist()
                    if len(names)!=len(set(names)):
                        raise ValueError('duplicate original C56 source member')
                    for filename in names:
                        match=C5_NAME.fullmatch(filename)
                        if not match:
                            raise ValueError('unexpected C56 original model path')
                        model_id=int(match.group(1))
                        label=f'p{model_id:03d}'
                        if label not in roster or label in verified or not low<=model_id<=high:
                            raise ValueError('wrong part, repeated or unknown source model')
                        info=source.getinfo(filename)
                        if not 0x78<=info.file_size<=MAX_SOURCE_BYTES:
                            raise ValueError('oversized or truncated C56 original model')
                        raw=source.read(filename)
                        digest=hashlib.sha256(raw).hexdigest()
                        if (digest!=refs[label]['sha256'] or
                            digest!=prior['models'][label]['source_sha256'] or
                            len(raw)!=int(refs[label]['decoded_bytes'])):
                            raise ValueError('SHA-256 C56 original source mismatch: '+label)
                        rig=rigs.read(f'skeleton/{label}.p3sk')
                        packed=pack_binding(model_id,raw,rig)
                        if packed:
                            count=struct.unpack_from('<H',packed,8)[0]
                            if count!=prior['models'][label]['original_named_transform_track_groups']:
                                raise ValueError('C147 original named track count mismatch')
                            output.writestr(f'track_bindings/{label}.p3tb',packed)
                            total+=count;models+=1
                        else:
                            if prior['models'][label]['original_named_transform_track_groups']:
                                raise ValueError('missing original animated nodes')
                            zero+=1
                        verified.add(label)
            if verified!=roster or total!=prior['source_C5_named_node_tracks_verified']:
                raise ValueError('incomplete 730-model original source track bindings')
        temp.replace(destination)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return {'source_models_sha_verified':len(verified),
            'private_p3tb_files':models,
            'original_track_owner_bindings_verified':total,
            'models_without_source_track_groups':zero,
            'original_clip_semantics_verified':False,
            'original_skinning_verified':False,
            'private_package_only':True}

def write_private_report(path,result):
    """Atomically write SHA-bearing audit output outside the public repository."""
    repo_root=Path(__file__).resolve().parents[1]
    requested=path.expanduser().absolute()
    parent=requested.parent.resolve()
    target=parent/requested.name
    if parent==repo_root or repo_root in parent.parents:
        raise ValueError('private animation report must be outside public repository')
    if target.is_symlink():
        raise ValueError('refusing symlink private report destination')
    parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        fd,name=tempfile.mkstemp(prefix='.c151-report-',suffix='.tmp',dir=parent)
        temporary=Path(name)
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            os.fchmod(stream.fileno(),0o600)
            json.dump(result,stream,indent=2)
            stream.write('\\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts',nargs=3,type=Path,required=True)
    parser.add_argument('--decoder-bundle',type=Path,required=True)
    parser.add_argument('--c147-summary',type=Path,required=True)
    parser.add_argument('--private-skeleton-zip',type=Path,required=True)
    parser.add_argument('--private-bindings-zip',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():
        parser.error('refuse to overwrite original private report')
    result=audit(args.parts,args.decoder_bundle,args.c147_summary,
                 args.private_skeleton_zip,args.private_bindings_zip)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
