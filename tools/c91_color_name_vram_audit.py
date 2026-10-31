#!/usr/bin/env python3
"""Source-only original color-name hints and DS VRAM capacity audit.

C88/C90 original indices are verified; source texture NAME patterns and
CF_COLORMAP flags do not prove 3DS GPU sampler-channel assignments.
DO NOT synthesize release P3MT bindings from this diagnostic evidence.
"""
import argparse,csv,json,re,struct,zlib,zipfile
from collections import defaultdict,Counter
from pathlib import Path

CAP=128*1024
COLOR=re.compile(r'Cl_ct[arb]$',re.I)
SIDECAR=re.compile(r'source_material_candidates/(p\d{3})\.p3mr$')

def source_color_hint(material):
    flags=material['source_shader_declaration'].split(';;;')[-1].split(',')
    if 'CF_COLORMAP' not in flags:return None
    hits=[(int(material['texture_ref'+str(i)]),material['texture_name'+str(i)])
          for i in (0,1) if COLOR.search(material['texture_name'+str(i)])]
    return hits[0] if len(hits)==1 else None

def parse_p3mr(raw,number):
    if len(raw)<16:raise ValueError('truncated P3MR')
    magic,version,model,tri,n,crc=struct.unpack_from('<4sHHHHI',raw)
    if magic!=b'P3MR' or version!=1 or model!=number or not 1<=tri<=600 or not 1<=n<=64:
        raise ValueError('invalid P3MR header')
    if len(raw)!=16+n*12 or zlib.crc32(raw[16:])!=crc:
        raise ValueError('P3MR checksum/length mismatch')
    rows=[];cursor=0
    for i in range(n):
        first,count,mat,t0,t1,mode=struct.unpack_from('<6H',raw,16+12*i)
        if not count or first!=cursor or count>tri-cursor or mode!=0x0c02:
            raise ValueError('P3MR range not source-matched')
        rows.append((mat,t0,t1,count))
        cursor+=count
    if cursor!=tri:raise ValueError('P3MR incomplete triangle coverage')
    return rows

def budget(sizes,cap=CAP):
    result={i:list(v) for i,v in sizes.items()}
    if len(result)>8:raise ValueError('DS texture unit capacity exceeded')
    for w,h in result.values():
        if any(x<8 or x>256 or x&(x-1) for x in (w,h)):
            raise ValueError('unsupported DS power-of-two texture dimensions')
    original=sum(w*h*2 for w,h in result.values());steps=0
    while sum(w*h*2 for w,h in result.values())>cap:
        choices=[(w*h,i) for i,(w,h) in result.items() if w>8 or h>8]
        if not choices:raise ValueError('minimum texture sizes exceed VRAM budget')
        _,which=max(choices)
        w,h=result[which]
        if w>=h and w>8:w//=2
        elif h>8:h//=2
        else:w//=2
        result[which]=[w,h];steps+=1
    return {'original_bytes':original,'planned_bytes':sum(w*h*2 for w,h in result.values()),
            'resizes':steps,'dimensions':result}

def read_index(path,key):
    rows=defaultdict(dict)
    with path.open(newline='',encoding='utf8') as f:
        for row in csv.DictReader(f):
            mid=row['model_id'];index=int(row[key])
            if index in rows[mid]:raise ValueError('duplicate original source record')
            rows[mid][index]=row
    return rows

def audit(material_path,texture_path,sidecars):
    materials=read_index(material_path,'material_index')
    textures=read_index(texture_path,'index')
    stats=Counter();rows=[];seen=set()
    with zipfile.ZipFile(sidecars) as z:
        if len(z.namelist())!=len(set(z.namelist())):
            raise ValueError('duplicate private source sidecar member')
        for filename in z.namelist():
            match=SIDECAR.fullmatch(filename)
            if not match:continue
            mid=match.group(1)
            if mid in seen:raise ValueError('duplicate model P3MR')
            seen.add(mid)
            ranges=parse_p3mr(z.read(filename),int(mid[1:]))
            selected={};unresolved=0
            for mat,t0,t1,count in ranges:
                original=materials[mid].get(mat)
                if original is None or (int(original['texture_ref0']),int(original['texture_ref1']))!=(t0,t1):
                    raise ValueError(mid+' original source material index mismatch')
                evidence=source_color_hint(original)
                if evidence is None:
                    unresolved+=1
                    continue
                idx,name=evidence
                tex=textures[mid].get(idx)
                if tex is None or tex['original_name']!=name:
                    raise ValueError(mid+' source-derived texture name mismatch')
                selected[idx]=(int(tex['ds_width']),int(tex['ds_height']))
            allocation=budget(selected)
            good=unresolved==0 and bool(selected)
            stats['examined_ranges']+=len(ranges)
            stats['unresolved_ranges']+=unresolved
            stats['candidate_models']+=int(good)
            stats['review_models']+=int(not good)
            stats['candidate_images']+=len(selected) if good else 0
            stats['models_needing_resize']+=int(good and allocation['resizes']>0)
            rows.append({'model_id':mid,'original_ranges':len(ranges),'ambiguous_ranges':unresolved,
                'candidate_color_textures':len(selected),'original_color_bytes':allocation['original_bytes'],
                'planned_color_bytes':allocation['planned_bytes'],'resizes':allocation['resizes'],
                'status':'COLOR_NAME_HINT_ONLY' if good else 'REQUIRES_SAMPLER_REVIEW',
                'sampler_role_verified':False,'p3mt_emitted':False})
    if len(seen)!=538:raise ValueError('expected 538 original C90 candidate sidecars')
    return {'models':len(seen),**stats,'verified_sampler_assignments':0,'p3mt_emitted':0},sorted(rows,key=lambda x:x['model_id'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--materials',required=True,type=Path)
    p.add_argument('--textures',required=True,type=Path)
    p.add_argument('--sidecars',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    summary,rows=audit(a.materials,a.textures,a.sidecars)
    a.out.write_text(json.dumps({'summary':summary,'models':rows,
        'limitation':'Sampler roles are candidate hints, NOT verified original GPU channels'},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
