#!/usr/bin/env python3
"""Recover verified (timestamp, float3) source channels from private C56 C5.

C143 identifies opaque 3-record groups. C144 establishes that the SECOND
and THIRD records encode little-endian 4-float rows: monotonically increasing
integral frame/time tags, followed by three finite float32 components. It does
NOT establish bone ID, transform channel roles, units, frame rate or interpolation.
It does not generate usable animation P3AN or material/texture assignments.
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

MODEL_NAME=re.compile(r'decoded_c5/p([0-9]{3})\.c5\Z')
MAX_C5_BYTES=16*1024*1024
MAX_KEYS_PER_VECTOR=2048
MAX_FRAME_TAG=1000000
EXTREME_COMPONENT_ABS=100000.0


def read_timed_vec3(raw:bytes, start:int, end:int, *, with_values=False):
    """Read 16-byte source records with all timing and finiteness verified."""
    if start<0 or end>len(raw) or end<=start or (end-start)%16:
        raise ValueError('invalid 16-byte time+float3 source span')
    count=(end-start)//16
    if not 2<=count<=MAX_KEYS_PER_VECTOR:
        raise ValueError('unexpected source time+float3 key count')
    previous=-1
    hasher=hashlib.sha256()
    extreme=0
    values=[]
    first_xyz=None
    last_xyz=None
    for idx, (t,x,y,z) in enumerate(struct.iter_unpack('<ffff', raw[start:end])):
        if not all(math.isfinite(n) for n in (t,x,y,z)):
            raise ValueError('nonfinite source time or vector')
        if not t.is_integer() or not 0<=t<=MAX_FRAME_TAG or t<=previous:
            raise ValueError('nonintegral, negative or unordered source time')
        if idx==0 and t!=0.0:
            raise ValueError('source vector channel does not start at time zero')
        previous=int(t)
        xyz=(x,y,z)
        if idx==0: first_xyz=xyz
        last_xyz=xyz
        extreme+=sum(abs(component)>EXTREME_COMPONENT_ABS for component in xyz)
        if with_values:
            values.append({'time_tag':int(t),'components':list(xyz)})
    hasher.update(raw[start:end])
    return {'keyframes':count,'end_time_tag':previous,
            'extreme_components':extreme,
            'source_payload_sha256':hasher.hexdigest(),
            'first_xyz':list(first_xyz),'last_xyz':list(last_xyz),
            **({'values':values} if with_values else {})}


def inspect_model(raw:bytes, *, detailed=False):
    prior=group_candidates(raw,detailed=False)
    start=struct.unpack_from('<I',raw,0x48)[0]
    strings=struct.unpack_from('<I',raw,0x64)[0]
    count=prior['source_track_records']
    entries=[struct.unpack_from('<4I',raw,start+16*i) for i in range(count)]
    i=0
    groups=[]
    count_by_role=[0,0]
    max_frame=0
    extrema=0
    exact_time_lists=0
    shared_final_time=0
    q_length_mod10=collections.Counter()
    frames=collections.Counter()
    while i+2<count:
        a,b,c=entries[i:i+3]
        matches=(tuple(row[3] for row in (a,b,c))==CHANNEL_CODES and
                 a[1]==b[1]==c[1] and
                 (a[2]&0xffff)==(b[2]&0xffff)==(c[2]&0xffff))
        if not matches:
            i+=1;continue
        nxt=entries[i+3][0] if i+3<count else strings
        qa_len=b[0]-a[0]
        q_length_mod10[str(qa_len%10)]+=1
        v1=read_timed_vec3(raw,b[0],c[0],with_values=detailed)
        v2=read_timed_vec3(raw,c[0],nxt,with_values=detailed)
        if v1['end_time_tag']==v2['end_time_tag']:
            shared_final_time+=1
        else:
            raise ValueError('paired C5 vector channels disagree on final time')
        # Comparing the exact integral timestamp arrays is separate from
        # validating individual stream monotonicity.
        tag1=[int(row[0]) for row in struct.iter_unpack('<ffff',raw[b[0]:c[0]])]
        tag2=[int(row[0]) for row in struct.iter_unpack('<ffff',raw[c[0]:nxt])]
        exact_time_lists+=tag1==tag2
        max_frame=max(max_frame,v1['end_time_tag'])
        frames[str(v1['end_time_tag'])]+=1
        extrema+=v1['extreme_components']+v2['extreme_components']
        count_by_role[0]+=v1['keyframes']
        count_by_role[1]+=v2['keyframes']
        if detailed:
            groups.append({
                'source_first_record':i,
                'opaque_owner':f'0x{a[1]:08x}',
                'opaque_channel_key_low16':f'0x{a[2]&0xffff:04x}',
                'first_channel_payload_bytes':qa_len,
                'first_channel_encoding_unverified':True,
                'timed_vector_channels':[v1,v2],
                'bone_role_verified':False,
                'animation_framerate_verified':False,
            })
        i+=3
    if count_by_role[0] < 2*prior['three_channel_candidates'] or len(groups)>prior['three_channel_candidates']:
        raise ValueError('C143 channel grouping and C144 decoded keys disagree')
    return {'source_track_records':count,
            'candidate_group_count':prior['three_channel_candidates'],
            'first_vector_keyframes':count_by_role[0],
            'second_vector_keyframes':count_by_role[1],
            'paired_final_timestamps_match':shared_final_time,
            'identical_full_timestamps':exact_time_lists,
            'maximum_time_tag':max_frame,
            'extreme_components_uninterpreted':extrema,
            'opaque_first_channel_length_mod10':dict(q_length_mod10),
            'group_duration_histogram':dict(frames),
            'source_track_payload_aggregate_sha256':prior['source_track_payload_aggregate_sha256'],
            'bone_attachment_verified':False,
            'channel_semantic_roles_verified':False,
            'animation_playback_rate_verified':False,
            **({'groups':groups} if detailed else {})}


def audit(parts,decoder_bundle,prior_report, *, detailed_model=None):
    if len(parts)!=3:
        raise ValueError('three source archives must be supplied in original C56 order')
    refs=reference_rows(decoder_bundle)
    prior=json.loads(Path(prior_report).read_text(encoding='utf-8'))
    if prior.get('c56_models_verified')!=730 or set(prior.get('models',{}))!=set(refs):
        raise ValueError('missing C143 original source provenance report')
    if detailed_model is not None and not re.fullmatch(r'p[0-9]{3}',detailed_model):
        raise ValueError('invalid selected private model label')
    models={}
    totals=collections.Counter()
    qmods=collections.Counter()
    extremes=[]
    for partition,path in enumerate(parts):
        low,high=PART_RANGES[partition]
        with zipfile.ZipFile(path) as z:
            names=z.infolist()
            if len(names)!=len({n.filename for n in names}):
                raise ValueError('ambiguous duplicate source ZIP member')
            for info in names:
                m=MODEL_NAME.fullmatch(info.filename)
                if not m: raise ValueError('unrecognized C5 source archive member')
                number=int(m.group(1));label=f'p{number:03d}'
                if number not in ROSTER or not low<=number<=high or label in models:
                    raise ValueError(f'out-of-order, duplicated or unsupported model {label}')
                if not 0x78<=info.file_size<=MAX_C5_BYTES:
                    raise ValueError(f'C5 source size out of bounds: {label}')
                raw=z.read(info)
                digest=hashlib.sha256(raw).hexdigest()
                previous=prior['models'][label]
                if (digest!=refs[label]['sha256'] or len(raw)!=int(refs[label]['decoded_bytes']) or
                    digest!=previous['source_sha256']):
                    raise ValueError(f'original source C56/C143 SHA mismatch: {label}')
                record=inspect_model(raw,detailed=(detailed_model==label))
                if (record['source_track_records']!=previous['source_track_records'] or
                    record['candidate_group_count']!=previous['three_channel_candidates'] or
                    record['source_track_payload_aggregate_sha256']!=previous['source_track_payload_aggregate_sha256']):
                    raise ValueError(f'original C143 track group identity mismatch: {label}')
                for key in ('candidate_group_count','first_vector_keyframes','second_vector_keyframes',
                            'paired_final_timestamps_match','identical_full_timestamps',
                            'extreme_components_uninterpreted'):
                    totals[key]+=record[key]
                for key,count in record['opaque_first_channel_length_mod10'].items():
                    qmods[key]+=count
                totals['max_time_tag']=max(totals['max_time_tag'],record['maximum_time_tag'])
                if record['extreme_components_uninterpreted']:
                    extremes.append(label)
                # Leave private detailed keyframes in a different, opt-in local report.
                models[label]={
                    'source_sha256':digest,
                    'group_count':record['candidate_group_count'],
                    'first_vector_keyframes':record['first_vector_keyframes'],
                    'second_vector_keyframes':record['second_vector_keyframes'],
                    'maximum_time_tag':record['maximum_time_tag'],
                    'extreme_components_uninterpreted':record['extreme_components_uninterpreted'],
                    **({'source_group_values':record['groups']} if detailed_model==label else {}),
                }
    if set(models)!=set(refs) or totals['candidate_group_count']!=prior.get('ordered_three_channel_candidates'):
        raise ValueError('C56/C143 model roster or group count mismatch')
    return {
        'c56_models_verified':len(models),
        'c143_ordered_groups_verified':totals['candidate_group_count'],
        'decoded_time_float3_streams':totals['candidate_group_count']*2,
        'first_time_float3_keyframes':totals['first_vector_keyframes'],
        'second_time_float3_keyframes':totals['second_vector_keyframes'],
        'total_time_float3_keyframes':totals['first_vector_keyframes']+totals['second_vector_keyframes'],
        'paired_final_timestamps_match':totals['paired_final_timestamps_match'],
        'identical_full_timestamp_lists':totals['identical_full_timestamps'],
        'maximum_source_time_tag':totals['max_time_tag'],
        'extreme_float_components_uninterpreted':totals['extreme_components_uninterpreted'],
        'models_with_extreme_components':extremes,
        'first_channel_payload_length_mod10_counts':dict(qmods),
        'precise_bone_transform_roles_verified':False,
        'animation_playback_rate_verified':False,
        'source_face_to_material_mapping_verified':False,
        'textures_enabled_by_recovery':0,
        'scope':'Verified second/third source stream <float32 timestamp, float32 x,y,z> records. Channel roles and first stream semantics are NOT decoded.',
        'models':dict(sorted(models.items())),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts',nargs=3,type=Path,required=True)
    p.add_argument('--decoder-bundle',type=Path,required=True)
    p.add_argument('--c143-summary',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--detailed-model',help='opt-in full private keyframe values for one model pNNN')
    args=p.parse_args()
    if args.report.exists():p.error('will not overwrite an existing private report')
    output=audit(args.parts,args.decoder_bundle,args.c143_summary,detailed_model=args.detailed_model)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in output.items() if k!='models'},indent=2))


if __name__=='__main__':main()