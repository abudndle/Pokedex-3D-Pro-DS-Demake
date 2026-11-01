#!/usr/bin/env python3
"""Decode original C5 10-byte (u16 time + biased u16x4) quaternion candidates.

All 730 source-model archives are SHA-verified against C56 and the C144
recovered vector report. This recovers byte-exact packed rotation-like key
records; it does not certify original skeletal attachments, 3DS interpolation,
material assignments or DS game playback.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
import re
import struct
import zipfile
from pathlib import Path
from c140_c5_shader_inventory import ROSTER, PART_RANGES, reference_rows
from c143_c5_channel_groups import CHANNEL_CODES, group_candidates

NAME=re.compile(r'decoded_c5/p([0-9]{3})\.c5\Z')
MAX_C5_BYTES=16*1024*1024
MAX_QUAT_KEYS=4096
MAX_TAG=1000000
MAX_NORMALIZATION_SQ_ERROR=.001


def packed_quaternions(raw:bytes, start:int, end:int, *, with_values=False):
    """Inspect a C5 10-byte keyed quaternion candidate + optional zero pad."""
    if start<0 or end>len(raw) or start>=end:
        raise ValueError('invalid quaternion source span')
    length=end-start
    remainder=length%10
    if remainder not in (0,2):
        raise ValueError('invalid 10-byte rotation-like record alignment')
    if remainder and raw[end-2:end]!=bytes(2):
        raise ValueError('nonzero or malformed rotation-like alignment padding')
    key_count=length//10
    if key_count<2 or key_count>MAX_QUAT_KEYS:
        raise ValueError('rotation-like key count out of safety bounds')
    maximum_error=0.0
    last_time=-1
    records=[]
    for t,c0,c1,c2,c3 in struct.iter_unpack('<5H',raw[start:start+key_count*10]):
        if t<=last_time or t>MAX_TAG:
            raise ValueError('unordered original packed time tags')
        if last_time<0 and t!=0:
            raise ValueError('original packed time does not start at zero')
        last_time=t
        q=tuple((v-32768)/32767.0 for v in (c0,c1,c2,c3))
        err=abs(sum(c*c for c in q)-1.0)
        if err>MAX_NORMALIZATION_SQ_ERROR:
            raise ValueError('packed quaternion candidate not normalized')
        maximum_error=max(maximum_error,err)
        if with_values:records.append({'time_tag':t,'normalized_components_source_order':list(q)})
    return {
        'source_quaternion_candidate_keys':key_count,
        'source_last_time_tag':last_time,
        'zero_alignment_padding_bytes':remainder,
        'max_squared_norm_error':maximum_error,
        'source_payload_sha256':hashlib.sha256(raw[start:end]).hexdigest(),
        'bone_transform_role_verified':False,
        **({'keys':records} if with_values else {}),
    }


def inspect_model(raw:bytes,*,detailed=False):
    prior=group_candidates(raw)
    count=prior['source_track_records']
    start=struct.unpack_from('<I',raw,0x48)[0]
    strings=struct.unpack_from('<I',raw,0x64)[0]
    entries=[struct.unpack_from('<4I',raw,start+16*i) for i in range(count)]
    keyframes=groups=padding=0
    max_error=0.0
    max_tag=0
    records=[]
    i=0
    while i+2<count:
        r=entries[i:i+3]
        if (tuple(x[3] for x in r)!=CHANNEL_CODES or
            len({x[1] for x in r})!=1 or
            len({x[2]&0xffff for x in r})!=1):
            i+=1;continue
        q=packed_quaternions(raw,r[0][0],r[1][0],with_values=detailed)
        next_start=entries[i+3][0] if i+3<count else strings
        last_vec_time=struct.unpack_from('<f',raw,next_start-16)[0]
        if not last_vec_time.is_integer() or q['source_last_time_tag']!=int(last_vec_time):
            raise ValueError('original packed quaternion and float3 source durations differ')
        groups+=1
        keyframes+=q['source_quaternion_candidate_keys']
        padding+=q['zero_alignment_padding_bytes']
        max_error=max(max_error,q['max_squared_norm_error'])
        max_tag=max(max_tag,q['source_last_time_tag'])
        if detailed:
            records.append({
                'source_first_track_index':i,
                'opaque_owner_word':f'0x{r[0][1]:08x}',
                'opaque_channel_key_low16':f'0x{r[0][2]&0xffff:04x}',
                **q,
            })
        i+=3
    if groups!=prior['three_channel_candidates']:
        raise ValueError('source C143 rotation group coverage inconsistent')
    return {
        'source_three_channel_groups':groups,
        'source_quaternion_candidate_keys':keyframes,
        'zero_alignment_padding_bytes':padding,
        'maximum_time_tag':max_tag,
        'max_squared_norm_error':max_error,
        'source_track_payload_aggregate_sha256':prior['source_track_payload_aggregate_sha256'],
        'original_bone_attachments_verified':False,
        **({'packed_groups':records} if detailed else {}),
    }


def audit(parts,decoder_bundle,c144_summary,*,detailed_model=None):
    if len(parts)!=3:
        raise ValueError('C56 requires three correctly ordered archives')
    refs=reference_rows(decoder_bundle)
    prior=json.loads(Path(c144_summary).read_text(encoding='utf-8'))
    if prior.get('c56_models_verified')!=730 or set(prior.get('models',{}))!=set(refs):
        raise ValueError('missing verified C144 source vector report')
    if detailed_model is not None and not re.fullmatch(r'p[0-9]{3}',detailed_model):
        raise ValueError('invalid selected private model label')
    models={}
    totals=collections.Counter()
    max_err=0.0
    for idx,path in enumerate(parts):
        low,high=PART_RANGES[idx]
        with zipfile.ZipFile(path) as z:
            entries=z.infolist()
            if len(entries)!=len({e.filename for e in entries}):
                raise ValueError('duplicate source archive members')
            for member in entries:
                m=NAME.fullmatch(member.filename)
                if not m:raise ValueError('unexpected source C5 archive member')
                number=int(m.group(1));label=f'p{number:03d}'
                if (number not in ROSTER or not low<=number<=high or
                    label in models or not 0x78<=member.file_size<=MAX_C5_BYTES):
                    raise ValueError(f'displaced/invalid source model: {label}')
                raw=z.read(member)
                digest=hashlib.sha256(raw).hexdigest()
                if (digest!=refs[label]['sha256'] or
                    len(raw)!=int(refs[label]['decoded_bytes']) or
                    digest!=prior['models'][label]['source_sha256']):
                    raise ValueError(f'C56/C144 source mismatch: {label}')
                decoded=inspect_model(raw,detailed=(detailed_model==label))
                if decoded['source_three_channel_groups']!=prior['models'][label]['group_count']:
                    raise ValueError(f'C144 original group coverage mismatch: {label}')
                totals['group_count']+=decoded['source_three_channel_groups']
                totals['quaternion_keyframes']+=decoded['source_quaternion_candidate_keys']
                totals['zero_alignment_padding_bytes']+=decoded['zero_alignment_padding_bytes']
                totals['max_time_tag']=max(totals['max_time_tag'],decoded['maximum_time_tag'])
                max_err=max(max_err,decoded['max_squared_norm_error'])
                models[label]={
                    'source_sha256':digest,
                    'source_group_count':decoded['source_three_channel_groups'],
                    'original_quaternion_candidate_keys':decoded['source_quaternion_candidate_keys'],
                    'source_alignment_padding_bytes':decoded['zero_alignment_padding_bytes'],
                    'maximum_source_time_tag':decoded['maximum_time_tag'],
                    **({'original_packed_rotation_candidates':decoded['packed_groups']} if detailed_model==label else {}),
                }
    if set(models)!=set(refs) or totals['group_count']!=prior.get('c143_ordered_groups_verified'):
        raise ValueError('missing C145 model or original group inventory')
    return {
        'c56_source_models_verified':len(models),
        'c144_channel_groups_verified':totals['group_count'],
        'decoded_packed_rotation_like_keyframes':totals['quaternion_keyframes'],
        'zero_alignment_padding_bytes_verified':totals['zero_alignment_padding_bytes'],
        'maximum_source_time_tag':totals['max_time_tag'],
        'maximum_normalization_squared_error':max_err,
        'packed_quaternion_encoding_consistent':True,
        'bone_hierarchy_verified':False,
        'source_animation_clip_boundaries_verified':False,
        'original_animation_fps_verified':False,
        'native_animation_activated':False,
        'new_original_texture_bindings':0,
        'scope':'Exact 10-byte u16 time+biased u16x4 quaternion candidates with optional 2-byte zero pad, not verified skeletal playback.',
        'models':dict(sorted(models.items()))
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts',nargs=3,type=Path,required=True)
    p.add_argument('--decoder-bundle',type=Path,required=True)
    p.add_argument('--c144-summary',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--detailed-model',help='owner-private complete source keyframes for ONE model label pNNN')
    args=p.parse_args()
    if args.report.exists():p.error('never overwrite a private report')
    result=audit(args.parts,args.decoder_bundle,args.c144_summary,detailed_model=args.detailed_model)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))

if __name__=='__main__':main()