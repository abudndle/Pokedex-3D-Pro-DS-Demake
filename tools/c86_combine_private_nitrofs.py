#!/usr/bin/env python3
"""Merge a private C84 NitroFS bundle with C86 validated fallback geometry.

No UV candidates installed automatically because their geometry differs from
C18 fallbacks. To test a UV candidate, copy its matching DS3M AND P3UV pair.
"""
import argparse
import collections
import hashlib
import json
import struct
import zipfile
from pathlib import Path

def combine(base, geom, target, report):
    summary={}
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(geom) as b, zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as out:
        old=set(a.namelist())
        if any(n.startswith('preview/') for n in old):
            raise ValueError('base ZIP preview collision')
        previews=[n for n in b.namelist() if n.startswith('preview/') and n.endswith('.ds3m')]
        if len(previews)!=726:
            raise ValueError('expected 726 validated original-derived DS3M files')
        for name in a.namelist():
            data=a.read(name)
            out.writestr(name,data)
        for name in sorted(previews):
            payload=b.read(name)
            magic,ver,n,source_vertices,source_faces=struct.unpack_from('<4sHHII',payload)
            if magic!=b'DS3M' or ver not in (1,2) or not (1<=n<=600) or source_faces<n:
                raise ValueError('malformed preview '+name)
            if len(payload)!=16+n*(21 if ver==2 else 18):
                raise ValueError('invalid preview byte length '+name)
            out.writestr(name,payload)
        out.writestr('C86_STAGING_README.txt',
             'C86 private NitroFS development stage. Includes original-derived C84 GUI,\n'
             'English Dex text, moves, 4039 texture payloads and 726 C18 DS3M geometry previews.\n'
             'Original C5 mesh-to-material bindings have NOT been recovered; no P3MT made.\n'
             '538 matching DS3M/P3UV UV CANDIDATE pairs are available in the separate\n'
             'C86 private geometry candidates archive, NOT auto-enabled here.\n'
             'Models 730-733 lack recovered C18 preview meshes.\n'
             'This is an INCOMPLETE development asset stage, NOT a final original game ROM.\n')
    with zipfile.ZipFile(target) as stage:
        bad=stage.testzip()
        if bad:raise ValueError('bad ZIP CRC: '+bad)
        name_list=stage.namelist()
        counts=collections.Counter(n.split('/')[0] for n in name_list)
        summary={'source':'C84 + verified C86 fallback original-derived C18 geometry',
                 'archive':target.name,'entries':len(name_list),'zip_bytes':target.stat().st_size,
                 'zip_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                 'category_counts':dict(counts),'fallback_geometry_previews':len(previews),
                 'complete_uv_candidates_staged_to_renderer':0,
                 'verified_original_material_bindings':0,
                 'release_ready':False}
        if counts['preview']!=726 or counts['textures']!=4039 or counts['catalogs']!=730 or counts['materials']!=726:
            raise ValueError('combined pack lost required original data')
    report.write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--geom',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(combine(args.base,args.geom,args.output,args.report),indent=2))