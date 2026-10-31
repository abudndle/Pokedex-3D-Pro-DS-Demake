#!/usr/bin/env python3
"""Public-safe P3UV/DS3M geometry-pair audit; never guesses materials."""
import argparse
import json
import re
import struct
import zipfile
from pathlib import Path

NAME = re.compile(r'(preview|uv_candidates)/p(\d{3})\.(ds3m|p3uv)$')
ROSTER = set(range(734)) - {721,722,723,724}

def inspect_ds3m(raw):
    if len(raw)<16:raise ValueError('truncated DS3M')
    magic,ver,n,vertices,faces=struct.unpack_from('<4sHHII',raw)
    if magic!=b'DS3M' or ver not in (1,2) or not 1<=n<=600 or not vertices or faces<n:
        raise ValueError('invalid DS3M header')
    if len(raw)!=16+n*(21 if ver==2 else 18):raise ValueError('DS3M size mismatch')
    xyz=struct.unpack_from('<'+'h'*(9*n),raw,16)
    if max(abs(x) for x in xyz)>=32767:raise ValueError('DS3M coordinate overflow')
    return n,vertices,faces

def inspect_uv(raw):
    if len(raw)<8:raise ValueError('truncated P3UV')
    magic,ver,count=struct.unpack_from('<4sHH',raw)
    if magic!=b'P3UV' or ver!=1 or not 1<=count<=600 or len(raw)!=8+count*12:
        raise ValueError('invalid P3UV header or size')
    return count

def audit(path,require_full=False):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(set(names))!=len(names):raise ValueError('duplicate ZIP members')
        previews={};ds_candidates={};uv_candidates={}
        for name in names:
            match=NAME.fullmatch(name)
            if not match:continue
            kind,raw_id,ext=match.groups()
            model=int(raw_id)
            if model not in ROSTER:raise ValueError('unexpected source model '+raw_id)
            if kind=='preview':
                if ext!='ds3m':raise ValueError('fallback preview cannot contain mismatched UV')
                previews[model]=inspect_ds3m(z.read(name))
            elif ext=='ds3m':
                ds_candidates[model]=inspect_ds3m(z.read(name))
            else:
                uv_candidates[model]=inspect_uv(z.read(name))
        if set(ds_candidates)!=set(uv_candidates):
            raise ValueError('missing matching DS3M/P3UV pair')
        for model,preview in ds_candidates.items():
            if preview[0]!=uv_candidates[model]:
                raise ValueError('triangle-count mismatch in UV pair: p%03d'%model)
            if model not in previews:
                raise ValueError('UV candidate lacks fallback model: p%03d'%model)
        if require_full and (len(previews)!=726 or len(ds_candidates)!=538):
            raise ValueError('incomplete C86 private 726+538 batch')
        return {'fallback_previews':len(previews),
                'paired_source_uv_candidates':len(ds_candidates),
                'source_model_roster':len(ROSTER),
                'models_missing_fallbacks':sorted(ROSTER-set(previews)),
                'original_material_bindings_verified':0,
                'visual_accuracy_verified':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--require-c86-full-batch',action='store_true')
    args=parser.parse_args()
    try:
        result=audit(args.archive,args.require_c86_full_batch)
    except (ValueError,OSError,struct.error,zipfile.BadZipFile) as exc:
        parser.exit(1,'C86 geometry pairing failed: %s\n'%exc)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
