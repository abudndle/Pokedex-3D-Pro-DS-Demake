#!/usr/bin/env python3
"""Resolve source-verified original C5 animation owner-to-name references.

The high 16 bits of the C5 track owner word are a relative string-table
pointer (including legitimate suffix-interned strings). This verifies source
node/transform names but not hierarchy parents, material joints or playback.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path
from c140_c5_shader_inventory import ROSTER,PART_RANGES,reference_rows
from c143_c5_channel_groups import CHANNEL_CODES
from c146_c5_owner_control_fields import inspect_model as inspect_controls

NAME=re.compile(r'decoded_c5/p([0-9]{3})\.c5\Z')
MAX_C5_BYTES=16*1024*1024
MAX_OWNER_STRING_OFFSET=16384
MAX_NODE_NAME_BYTES=96


def resolve_string(raw:bytes, string_start:int, relative_offset:int):
    """Bounded C5 null-terminated ASCII reference; preserve suffix pointers."""
    pos=string_start+relative_offset
    if (string_start<0x78 or string_start>=len(raw) or
        relative_offset>MAX_OWNER_STRING_OFFSET or pos>=len(raw)):
        raise ValueError('original C5 node string pointer outside source table')
    end=raw.find(b'\0',pos,min(len(raw),pos+MAX_NODE_NAME_BYTES+1))
    if end<0 or end==pos:
        raise ValueError('empty or unterminated source node string')
    name=raw[pos:end]
    if not all(32<=c<=126 for c in name):
        raise ValueError('nonprintable original C5 node name')
    suffix=bool(relative_offset and raw[pos-1]!=0)
    if suffix:
        # A suffix-reference is legitimate only inside a printable source
        # string, with a preceding NUL-delimited start. Do NOT shift the
        # pointer backward and silently choose a different bone name.
        prev_nul=raw.rfind(b'\0',string_start,pos)
        base=prev_nul+1 if prev_nul>=0 else string_start
        if (base>=pos or pos-base>MAX_NODE_NAME_BYTES or
            not all(32<=x<=126 for x in raw[base:pos])):
            raise ValueError('invalid original suffix-interned C5 name')
    return name.decode('ascii'),suffix


def inspect_model(raw:bytes, *, detailed=False):
    proven=inspect_controls(raw,detailed=False)
    start=struct.unpack_from('<I',raw,0x48)[0]
    strings=struct.unpack_from('<I',raw,0x64)[0]
    end=struct.unpack_from('<I',raw,0x4c)[0]
    rr=[struct.unpack_from('<4I',raw,i) for i in range(start,end,16)]
    names=set();source_names=[];suffix_count=0;records=[]
    for i in range(len(rr)):
        if rr[i][3]!=CHANNEL_CODES[0]:continue
        if i+2>=len(rr) or tuple(x[3] for x in rr[i:i+3])!=CHANNEL_CODES:
            raise ValueError('unpaired original C5 name owner channel')
        owner=rr[i][1]
        token=owner&0xffff
        offset=owner>>16
        node_name,suffix=resolve_string(raw,strings,offset)
        if node_name in names:
            raise ValueError('multiple distinct original track groups resolve to the same named node')
        names.add(node_name)
        source_names.append(node_name)
        suffix_count+=suffix
        if detailed:
            records.append({'source_first_track_record':i,
                            'source_owner_token':token,
                            'name_offset_in_original_C5_strings':offset,
                            'original_node_name':node_name,
                            'source_uses_string_suffix_interning':suffix,
                            'bone_parent_verified':False,
                            'mesh_skin_binding_verified':False})
    if len(names)!=proven['candidate_groups']:
        raise ValueError('original named source group inventory incomplete')
    return {'source_named_channel_groups':len(names),
            'source_string_start_references':len(names)-suffix_count,
            'source_interned_string_suffix_references':suffix_count,
            'all_original_node_labels_unique':True,
            'source_owner_control_count_verified':proven['candidate_groups'],
            'original_bone_hierarchy_proven':False,
            **({'original_source_named_node_tracks':records} if detailed else {})}


def audit(parts,decoder_bundle,c146_summary, *, detailed_model=None):
    if len(parts)!=3:raise ValueError('exactly three original source archives required')
    refs=reference_rows(decoder_bundle)
    prior=json.loads(Path(c146_summary).read_text(encoding='utf-8'))
    if prior.get('c56_models_verified')!=730 or set(prior.get('models',{}))!=set(refs):
        raise ValueError('original C146 verified model inventory missing')
    if detailed_model is not None and not re.fullmatch(r'p[0-9]{3}',detailed_model):
        raise ValueError('invalid selected private model')
    models={};groups=0;interned=0;model_count=0
    for index,path in enumerate(parts):
        lo,hi=PART_RANGES[index]
        with zipfile.ZipFile(path) as z:
            items=z.infolist()
            if len(items)!=len({entry.filename for entry in items}):
                raise ValueError('duplicate original archive model')
            for file in items:
                m=NAME.fullmatch(file.filename)
                if not m:raise ValueError('unknown original C56 member')
                index=int(m.group(1));label=f'p{index:03d}'
                if (index not in ROSTER or not lo<=index<=hi or label in models or
                    not 0x78<=file.file_size<=MAX_C5_BYTES):
                    raise ValueError('displaced, duplicated or oversized C56 source model')
                raw=z.read(file);digest=hashlib.sha256(raw).hexdigest()
                if (digest!=refs[label]['sha256'] or len(raw)!=int(refs[label]['decoded_bytes']) or
                    digest!=prior['models'][label]['source_sha256']):
                    raise ValueError(f'C56/C146 original digest mismatch: {label}')
                result=inspect_model(raw,detailed=(label==detailed_model))
                if result['source_named_channel_groups']!=prior['models'][label]['source_groups']:
                    raise ValueError(f'original source named track coverage mismatch: {label}')
                model_count+=1;groups+=result['source_named_channel_groups']
                interned+=result['source_interned_string_suffix_references']
                models[label]={'source_sha256':digest,
                               'original_named_transform_track_groups':result['source_named_channel_groups'],
                               'names_resolving_to_interned_suffixes':result['source_interned_string_suffix_references'],
                               'source_names_unique':True,
                               **({'named_tracks':result['original_source_named_node_tracks']} if label==detailed_model else {})}
    if model_count!=730 or set(models)!=set(refs) or groups!=prior['source_c5_groups_verified']:
        raise ValueError('source named node audit incomplete')
    return {'original_C56_models_verified':model_count,
            'source_C5_named_node_tracks_verified':groups,
            'original_string_start_references':groups-interned,
            'source_interned_suffix_name_references':interned,
            'models_with_unique_source_track_node_names':model_count,
            'bone_name_association_source_verified':True,
            'bone_parent_hierarchy_verified':False,
            'source_mesh_skin_weights_verified':False,
            'original_action_clip_binding_verified':False,
            'original_DS_skeletal_animation_enabled':False,
            'scope':'C5 owner high16 points into original source string table, sometimes a string suffix. Names verified, hierarchy/skin binding NOT recovered.',
            'models':dict(sorted(models.items()))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parts',nargs=3,type=Path,required=True)
    p.add_argument('--decoder-bundle',type=Path,required=True)
    p.add_argument('--c146-summary',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--detailed-model')
    args=p.parse_args()
    if args.report.exists():p.error('refuse to overwrite original report')
    result=audit(args.parts,args.decoder_bundle,args.c146_summary,detailed_model=args.detailed_model)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2))

if __name__=='__main__':main()