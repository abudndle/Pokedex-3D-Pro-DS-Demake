#!/usr/bin/env python3
"""Local-only audited Pokédex 3D Pro recovery inputs; publishes NO original assets.

The JSON report describes verification coverage, not proof of a finished port.
This tool operates on owner-supplied decrypted archives in a PRIVATE workspace.
"""
import argparse, csv, hashlib, io, json, re, stat, struct, zipfile, zlib
from pathlib import Path
from collections import Counter

ROSTER = {n for n in range(734) if n not in (721,722,723,724)}
CHANNEL_CODES=(0x00040071,0x00030053,0x00030054)
ARCHIVES = [
 'Pokedex3D_C18_Forms_Models_Provisional_Color_Source.zip',
 'Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip',
 'Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip',
 'Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip',
 'Pokedex3D_C56_Decoder_Tools_and_Validation.zip',
 'Pokedex3D_C62_528_UV_Model_Exports.zip',
 'Pokedex3D_C63_Partial_UV_Recovery_162_Models.zip',
 'C86_PRIVATE_DS_GEOMETRY_AND_UV_CANDIDATES.zip',
 'C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip',
 'C141_PRIVATE_CORRECTED_SOURCE_COUNT_NITROFS.zip',
 'C136_PRIVATE_49_UNIT_UV_QA_NITROFS.zip',
 'C148_PRIVATE_730_ORIGINAL_SKELETON_P3SK.zip',
 'C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip',
 'C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip',
]

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()

def find(root,name):
    for p in (root/name,root/'files'/name,root/'archives'/name):
        if p.is_file():return p
    return None

def audit_zip(path, crc=True):
    with zipfile.ZipFile(path) as z:
        entries=z.infolist();names=[v.filename for v in entries]
        if len(names)!=len(set(names)):raise ValueError('duplicate ZIP paths: '+path.name)
        for item in entries:
            v=item.filename
            if not v or v.startswith('/') or '\\' in v or '..' in v.split('/') or stat.S_ISLNK(item.external_attr>>16):
                raise ValueError('unsafe archive entry: '+v)
        bad=z.testzip() if crc else None
        if bad:raise ValueError(f'corrupt archive {path.name}: {bad}')
        return {'sha256':digest(path),'size_bytes':path.stat().st_size,
                'zip_entries':len(entries),'uncompressed_bytes':sum(x.file_size for x in entries),
                'zip_full_crc_passed':bool(crc),'private_only':True}

def c56_refs(bundle):
    with zipfile.ZipFile(bundle) as z:
        b=z.read('C56_validation.csv').decode('utf8')
    ref={r['model']:r for r in csv.DictReader(io.StringIO(b))}
    if len(ref)!=730:raise ValueError('C56 baseline has wrong number of records')
    return ref

def read_p3sk(blob,model,raw):
    if len(blob)<20:raise ValueError('short skeleton')
    magic,v,m,n,roots,ns,crc=struct.unpack_from('<4sHHHHII',blob)
    if magic!=b'P3SK' or v!=1 or m!=model or not 1<=n<=160 or not 1<=roots<=n or not 1<=ns<=4096:
        raise ValueError('skeleton header invalid')
    if len(blob)!=20+n*56+ns or zlib.crc32(blob[20:])&0xffffffff !=crc:
        raise ValueError('skeleton CRC/length invalid')
    records=blob[20:20+n*56];strings=blob[20+n*56:];seenroots=0
    header_count=struct.unpack_from('<I',raw,0x10)[0]>>16
    start=struct.unpack_from('<I',raw,0x38)[0]
    stop=struct.unpack_from('<I',raw,0x3c)[0]
    strings_start=struct.unpack_from('<I',raw,0x64)[0]
    if n!=header_count or stop-start!=n*56 or records!=raw[start:stop] or strings!=raw[strings_start:strings_start+ns]:
        raise ValueError('native P3SK is not byte-exact source node data')
    for idx in range(n):
        node=records[idx*56:(idx+1)*56]
        parent,kind,name=struct.unpack_from('<HHI',node,48)
        if kind!=1 or (parent!=65535 and parent>=idx) or name>=ns:
            raise ValueError('skeleton node invalid')
        if parent==65535:seenroots+=1
        if not any(strings[j]==0 for j in range(name,min(ns,name+97))):
            raise ValueError('skeleton name not terminated')
        for j in range(12):
            bits=struct.unpack_from('<I',node,j*4)[0]
            if bits&0x7f800000==0x7f800000:raise ValueError('nonfinite source matrix')
    if seenroots!=roots:raise ValueError('skeleton root mismatch')
    return n,roots

def get_report(root,name):
    for p in (root/name,root/'reports'/name):
        if p.is_file():return json.loads(p.read_text(encoding='utf-8'))
    raise FileNotFoundError('missing private recovery report '+name)

def audit_c84_content(root):
    source=find(root,'C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip')
    target=root/'recovered'/'C84_CONTENT_RECOVERED_FROM_C86_NOT_ORIGINAL_ARCHIVE.zip'
    if source is None or not target.is_file():return {'available':False,'verified':False}
    with zipfile.ZipFile(source) as original,zipfile.ZipFile(target) as recovered:
        expect={name for name in original.namelist() if not name.startswith('preview/') and name!='C86_STAGING_README.txt'}
        if expect!=set(recovered.namelist()) or len(recovered.namelist())!=len(expect):
            raise ValueError('C84 recovered-original member roster mismatch')
        for name in expect:
            if original.read(name)!=recovered.read(name):raise ValueError('C84 recovered asset mismatch: '+name)
        source_manifest=json.loads(original.read('PRIVATE_STAGE_C84_MANIFEST.json'))
        for name,sha in source_manifest['original_gui_sha256'].items():
            if hashlib.sha256(recovered.read(name)).hexdigest()!=sha:
                raise ValueError('C84 source UI SHA mismatch: '+name)
        if hashlib.sha256(recovered.read('moves.p3dm')).hexdigest()!=source_manifest['moves_sha256']:
            raise ValueError('C84 original moves SHA mismatch')
    return {'available':True,'verified':True,'members_compared':len(expect),
        'original_C84_ZIP_recovered':False,'embedded_C84_UI_and_moves_SHA256_verified':True}

def verify(root):
    found={}; missing=[]
    for name in ARCHIVES:
        p=find(root,name)
        if p is None:
            missing.append(name)
        else:
            found[name]=audit_zip(p)
    req=['Pokedex3D_C56_Decoded_C5_Part_%d_of_3.zip'%i for i in (1,2,3)]
    base='Pokedex3D_C56_Decoder_Tools_and_Validation.zip'
    preview='C141_PRIVATE_CORRECTED_SOURCE_COUNT_NITROFS.zip'
    skel='C148_PRIVATE_730_ORIGINAL_SKELETON_P3SK.zip'
    uv='C136_PRIVATE_49_UNIT_UV_QA_NITROFS.zip'
    if not all(x in found for x in [*req,base,preview,skel,uv]):
        raise ValueError('required original C56 / native preview / rig / UV archive missing')
    refs=c56_refs(find(root,base))
    c141=get_report(root,'C141_PRIVATE_REPAIRED_VERIFICATION.json')
    c140=get_report(root,'C140_PRIVATE_C5_SHADER_DECLARATION_INVENTORY.json')
    c143=get_report(root,'C143_PRIVATE_CHANNEL_GROUP_SUMMARY.json')
    totals=Counter(); roster=set(); errors=[]; model_checks=[]
    with zipfile.ZipFile(find(root,preview)) as nz,zipfile.ZipFile(find(root,uv)) as uz,zipfile.ZipFile(find(root,skel)) as sz:
        np=set(nz.namelist()); un=set(uz.namelist()); sn=set(sz.namelist())
        textures=sorted(n for n in np if re.fullmatch(r'textures/p\d{3}/t\d{3}\.p3px',n))
        totals['texture_payloads']=len(textures)
        for name in textures:
            with nz.open(name) as f:h=f.read(10)
            if len(h)!=10 or h[:4]!=b'P3PX':raise ValueError('bad P3PX: '+name)
            _,ver,w,hgt=struct.unpack('<4sHHH',h)
            if ver not in (1,2) or w not in (8,16,32,64,128,256,512,1024) or hgt not in (8,16,32,64,128,256,512,1024) or nz.getinfo(name).file_size !=10+2*w*hgt:
                raise ValueError('invalid P3PX dims: '+name)
        # Observe, do not infer shader/material assignments.
        source_bindings=sum(1 for n in np if re.fullmatch(r'materials/p\d{3}\.(p3mr|p3sc|p3sw|p3mt)',n))
        totals['source_material_binding_sidecars']=source_bindings
        totals['upper_screen_ui_pages']=sum(bool(re.fullmatch(r'ui/pages/t0_\d\d_.*\.rgb555',n)) for n in np)
        totals['lower_screen_ui_pages']=sum(bool(re.fullmatch(r'ui/pages/t1_\d\d_.*\.rgb555',n)) for n in np)
        for part in req:
            with zipfile.ZipFile(find(root,part)) as z:
                for entry in z.infolist():
                    m=re.fullmatch(r'decoded_c5/p(\d{3})\.c5',entry.filename)
                    if not m:raise ValueError('unexpected C56 C5 record')
                    model=int(m.group(1)); label=f'p{model:03d}'
                    if model not in ROSTER or model in roster:raise ValueError('duplicate/out-of-range model')
                    raw=z.read(entry)
                    if len(raw)!=int(refs[label]['decoded_bytes']) or hashlib.sha256(raw).hexdigest()!=refs[label]['sha256']:
                        raise ValueError('C56 source hash mismatch: '+label)
                    if c140['models'][label]['source_c5_sha256']!=refs[label]['sha256'] or c141['models'][label]['source_sha256']!=refs[label]['sha256'] or c143['models'][label]['source_sha256']!=refs[label]['sha256']:
                        raise ValueError('provenance report hash mismatch: '+label)
                    path=f'preview/{label}.ds3m'
                    if path not in np or path not in un or f'skeleton/{label}.p3sk' not in sn:
                        raise ValueError('missing original preview or skeleton '+label)
                    b=nz.read(path);q=uz.read(path)
                    if len(b)<16:raise ValueError('truncated DS3M')
                    mag,ver,tri,reserved,total=struct.unpack_from('<4sHHII',b)
                    if mag!=b'DS3M' or ver not in (1,2) or not 1<=tri<=600 or reserved!=0 or total<tri or len(b)!=16+tri*(21 if ver==2 else 18):
                        raise ValueError('native DS3M format invalid '+label)
                    if total!=c141['models'][label]['source_triangle_count'] or tri!=c141['models'][label]['preview_triangles']:
                        raise ValueError('native C5 preview triangle mismatch '+label)
                    if len(q)<16:
                        raise ValueError('truncated QA DS3M '+label)
                    qmagic,qver,qtri,qreserved,qtotal=struct.unpack_from('<4sHHII',q)
                    if (qmagic!=b'DS3M' or qver not in (1,2) or qreserved!=0 or
                        not 1<=qtri<=600 or qtotal<qtri or
                        len(q)!=16+qtri*(21 if qver==2 else 18)):
                        raise ValueError('invalid QA native DS3M '+label)
                    qa_uv=f'preview/{label}.p3uv' in un
                    if q!=b:
                        if qa_uv:
                            if qtotal!=total:raise ValueError('QA UV source-triangle mismatch '+label)
                            totals['qa_uv_replaced_preview_models']+=1
                        elif model==561 and q[0:12]==b[0:12] and q[16:]==b[16:] and qtotal==2728 and total==3668:
                            totals['qa_stale_p561_source_count_only']+=1
                        else:
                            raise ValueError('unexpected QA preview differs '+label)
                    if qa_uv and qtri<=0:raise ValueError('QA UV model unavailable '+label)
                    nodes,roots=read_p3sk(sz.read(f'skeleton/{label}.p3sk'),model,raw)
                    track_start,track_end=struct.unpack_from('<I',raw,0x48)[0],struct.unpack_from('<I',raw,0x4c)[0]
                    strings_start=struct.unpack_from('<I',raw,0x64)[0]
                    if (track_end-track_start)%16:raise ValueError('invalid original track table width')
                    group_count=0
                    # Verify original animation group -> exact source node ID & same name offset.
                    records=[struct.unpack_from('<4I',raw,at) for at in range(track_start,track_end,16)]
                    i=0
                    while i+2<len(records):
                        trio=records[i:i+3]
                        if tuple(rec[3] for rec in trio)!=CHANNEL_CODES:
                            i+=1;continue
                        if len({rec[1] for rec in trio})!=1 or len({rec[2]&65535 for rec in trio})!=1:
                            raise ValueError('source animation owner mismatch '+label)
                        owner=trio[0][1]; node=owner&65535;name=owner>>16
                        if node>=nodes or struct.unpack_from('<I',raw,struct.unpack_from('<I',raw,0x38)[0]+node*56+52)[0]!=name:
                            raise ValueError('animated source node id/name does not match C5 rig '+label)
                        if strings_start+name>=len(raw):raise ValueError('node name offset outside C5')
                        group_count+=1;i+=3
                    if group_count!=c143['models'][label]['three_channel_candidates']:
                        raise ValueError('source track count mismatch '+label)
                    totals['models_verified']+=1;totals['preview_triangles']+=tri
                    totals['original_source_triangles']+=total
                    totals['original_skeleton_nodes']+=nodes;totals['original_skeleton_roots']+=roots
                    totals['verified_animation_to_node_links']+=group_count
                    roster.add(model)
                    model_checks.append({'model':label,'c56_sha256':refs[label]['sha256'],
                       'source_triangles':total,'ds3m_preview_triangles':tri,
                       'skeleton_nodes':nodes,'skeleton_roots':roots,
                       'named_animation_to_node_links':group_count,
                       'source_texture_binding_verified':False,
                       'original_mesh_skin_weights_verified':False})
        if roster!=ROSTER:raise ValueError('730-model roster incomplete')
        for name in sorted(un):
            if re.fullmatch(r'preview/p\d{3}\.p3uv',name):
                model=int(name[9:12]); b=uz.read(name)
                if len(b)<8 or b[:4]!=b'P3UV':raise ValueError('invalid UV '+name)
                _,version,count=struct.unpack_from('<4sHH',b)
                triangles=struct.unpack_from('<H',uz.read(f'preview/p{model:03d}.ds3m'),6)[0]
                if version!=1 or count!=triangles or len(b)!=8+12*count:raise ValueError('P3UV pair mismatch '+name)
                vals=struct.unpack_from('<'+'h'*(6*count),b,8)
                if any(v<0 or v>4096 for v in vals):raise ValueError('UV outside safe unit range '+name)
                totals['unit_uv_companions']+=1
        if totals['unit_uv_companions']!=49:raise ValueError('49 source UV companions not recovered')
    return {'result':'PASS','private_only':True,'publication_scope':'SHA-256 manifests and source-only QA; no original model or artwork binaries',
            'archive_inventory':found,'archives_unavailable':missing,
            'C84_embedded_original_content_recovery':audit_c84_content(root),
            'source_hashes_verified':totals['models_verified'],
            'checks':dict(totals),'model_checks':model_checks,
            'original_3ds_texture_binding_verified':False,
            'original_skeletal_skinning_verified':False,
            'asset_integrated_ARM9_emulator_verified':False,
            'missing_steps':['original per-face material/sampler mappings','original mesh skin weights','source action clip bindings','asset-integrated DS emulator visual/gameplay QA']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    result=verify(args.root)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('archive_inventory','model_checks')},indent=2))
if __name__=='__main__':main()