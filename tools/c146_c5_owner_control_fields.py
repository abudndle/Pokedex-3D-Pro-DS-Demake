#!/usr/bin/env python3
"""Verify source C5 group control-word counts, duration and owner identity.

The low 16 bits of C5 group control word 2 exactly equal the shared source
end time tag; the high 16 bits equal the first packed channel's key count.
Each model has distinct low-16 owner tokens. These are NOT proven skeleton
bone identifiers, hierarchy edges, material ranges or sampler assignments.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path
from c140_c5_shader_inventory import ROSTER,PART_RANGES,reference_rows
from c143_c5_channel_groups import CHANNEL_CODES,group_candidates

NAME=re.compile(r'decoded_c5/p([0-9]{3})\.c5\Z')
MAX_C5_BYTES=16*1024*1024


def inspect_model(raw:bytes, *, detailed=False):
    old=group_candidates(raw)
    start=struct.unpack_from('<I',raw,0x48)[0]
    end_str=struct.unpack_from('<I',raw,0x64)[0]
    n=old['source_track_records']
    records=[struct.unpack_from('<4I',raw,start+16*i) for i in range(n)]
    owners=set();source_order=[];quats=0;found=0;details=[];maximum_owner=0
    i=0
    while i+2<n:
        trio=records[i:i+3]
        if (tuple(r[3] for r in trio)!=CHANNEL_CODES or
            len({r[1] for r in trio})!=1 or
            len({r[2]&65535 for r in trio})!=1):
            i+=1;continue
        first,second,third=trio
        qlength=second[0]-first[0]
        qcount=qlength//10
        if qlength%10 not in (0,2) or qcount<2:
            raise ValueError('invalid original packed quaternion span')
        word=first[2]
        hi,lo=word>>16,word&65535
        stop=records[i+3][0] if i+3<n else end_str
        finaltime=struct.unpack_from('<f',raw,stop-16)[0]
        qlast=struct.unpack_from('<H',raw,first[0]+10*(qcount-1))[0]
        if (hi!=qcount or not finaltime.is_integer() or
            lo!=int(finaltime) or qlast!=lo):
            raise ValueError('source C5 control word count/time tag mismatch')
        # This is a C5 node-owner TOKEN candidate only, not a proven bone ID.
        owner=first[1]&65535
        if not owner or owner in owners:
            raise ValueError('duplicate/invalid source owner token within model')
        owners.add(owner)
        source_order.append(owner)
        maximum_owner=max(maximum_owner,owner)
        found+=1;quats+=qcount
        if detailed:
            details.append({'source_first_record':i,
                            'opaque_owner_word':f'0x{first[1]:08x}',
                            'owner_token_low16_uninterpreted':owner,
                            'high16_source_q_key_count':hi,
                            'low16_source_end_time_tag':lo,
                            'semantic_bone_id_verified':False})
        i+=3
    if found!=old['three_channel_candidates']:
        raise ValueError('C143 source group count mismatch')
    return {'candidate_groups':found,
            'packed_quaternion_keyframes':quats,
            'unique_owner_tokens':len(owners),
            'owner_tokens_strictly_increasing':all(source_order[j]<source_order[j+1] for j in range(len(source_order)-1)),
            'first_owner_token_is_one':bool(source_order) and source_order[0]==1,
            'largest_owner_token':maximum_owner,
            'source_owner_tokens_are_bone_ids_verified':False,
            **({'source_group_control_records':details} if detailed else {})}


def audit(parts,decoder_bundle,c145_summary, *, detailed_model=None):
    if len(parts)!=3:raise ValueError('expected three C56 source archives')
    ref=reference_rows(decoder_bundle)
    prior=json.loads(Path(c145_summary).read_text(encoding='utf-8'))
    if prior.get('c56_source_models_verified')!=730 or set(prior.get('models',{}))!=set(ref):
        raise ValueError('C145 recovered model baseline missing')
    if detailed_model is not None and not re.fullmatch(r'p[0-9]{3}',detailed_model):
        raise ValueError('invalid detailed-model label')
    models={}
    sums={'groups':0,'qkeys':0,'models_unique':0,'models_ordered':0,'first_one':0,'max_owner':0}
    for index,path in enumerate(parts):
        lo,hi=PART_RANGES[index]
        with zipfile.ZipFile(path) as z:
            entries=z.infolist()
            if len(entries)!=len({e.filename for e in entries}):
                raise ValueError('duplicate source ZIP entries')
            for member in entries:
                m=NAME.fullmatch(member.filename)
                if not m:raise ValueError('unrecognized original C5 ZIP member')
                idx=int(m.group(1));label=f'p{idx:03d}'
                if idx not in ROSTER or not lo<=idx<=hi or label in models or not 0x78<=member.file_size<=MAX_C5_BYTES:
                    raise ValueError('displaced or malformed original C56 model')
                raw=z.read(member);digest=hashlib.sha256(raw).hexdigest()
                if (digest!=ref[label]['sha256'] or len(raw)!=int(ref[label]['decoded_bytes']) or
                    digest!=prior['models'][label]['source_sha256']):
                    raise ValueError(f'C56/C145 original source digest mismatch: {label}')
                item=inspect_model(raw,detailed=(label==detailed_model))
                if (item['candidate_groups']!=prior['models'][label]['source_group_count'] or
                    item['packed_quaternion_keyframes']!=prior['models'][label]['original_quaternion_candidate_keys']):
                    raise ValueError(f'C145 source channel key totals mismatch: {label}')
                sums['groups']+=item['candidate_groups'];sums['qkeys']+=item['packed_quaternion_keyframes']
                sums['models_unique']+=item['unique_owner_tokens']==item['candidate_groups']
                sums['models_ordered']+=item['owner_tokens_strictly_increasing']
                sums['first_one']+=item['first_owner_token_is_one']
                sums['max_owner']=max(sums['max_owner'],item['largest_owner_token'])
                models[label]={'source_sha256':digest,'source_groups':item['candidate_groups'],
                               'unique_owner_tokens':item['unique_owner_tokens'],
                               'source_owner_order_is_sorted':item['owner_tokens_strictly_increasing'],
                               'largest_owner_token':item['largest_owner_token'],
                               **({'source_group_controls':item['source_group_control_records']} if label==detailed_model else {})}
    if set(models)!=set(ref) or sums['groups']!=prior['c144_channel_groups_verified'] or sums['qkeys']!=prior['decoded_packed_rotation_like_keyframes']:
        raise ValueError('C145 source model or key totals mismatch')
    return {'c56_models_verified':len(models),'source_c5_groups_verified':sums['groups'],
            'source_rotation_like_keys_verified':sums['qkeys'],
            'control_high16_equals_packed_key_count':sums['groups'],
            'control_low16_equals_common_end_time_tag':sums['groups'],
            'models_with_unique_owner_tokens':sums['models_unique'],
            'models_with_strictly_sorted_owner_tokens':sums['models_ordered'],
            'models_with_first_owner_token_one':sums['first_one'],
            'max_owner_token_observed':sums['max_owner'],
            'owner_tokens_proven_skeleton_bone_ids':False,
            'hierarchy_edges_verified':0,'animation_activated_on_ds':False,
            'original_material_face_mapping_proven':False,
            'scope':'Verified C5 source controls for packed quaternion count, time duration and unique per-model opaque owner tokens; not bone hierarchy.',
            'models':dict(sorted(models.items()))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts',nargs=3,type=Path,required=True)
    p.add_argument('--decoder-bundle',type=Path,required=True)
    p.add_argument('--c145-summary',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--detailed-model')
    args=p.parse_args()
    if args.report.exists():p.error('refusing to overwrite previous report')
    result=audit(args.parts,args.decoder_bundle,args.c145_summary,detailed_model=args.detailed_model)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))
if __name__=='__main__':main()