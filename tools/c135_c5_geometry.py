#!/usr/bin/env python3
"""C135 source-only C7 geometric recovery: contiguous mesh data and index scan.
Strictly validates counts, edge incidence, vertex XYZ, face area and OBJ references.
Does not infer texture images or unclassified vertex attributes.
"""
from collections import Counter
import numpy as np
from c5_dual_table_parser import parse
def inspect_faces(vals, nverts):
    if len(vals) % 3 or not vals:
        raise ValueError('source index buffer is not triangular')
    if min(vals) < 0 or max(vals) >= nverts or len(set(vals)) != nverts:
        raise ValueError('source index buffer out of range or incomplete')
    faces = [tuple(vals[i:i + 3]) for i in range(0, len(vals), 3)]
    if any(len(set(face)) != 3 for face in faces):
        raise ValueError('source face has repeated vertex')
    edges = Counter(tuple(sorted((a, b))) for a, b, c in faces
                    for a, b in ((a, b), (b, c), (c, a)))
    if any(count > 2 for count in edges.values()):
        raise ValueError('nonmanifold source topology')
    return faces, {'triangles': len(faces), 'boundary_edges':
                   sum(count == 1 for count in edges.values())}


MAX_GAP=16

def candidates_first(data, nverts, nidx):
    for parity in (0,1):
        a=np.frombuffer(data,dtype='<u2',offset=parity,count=(len(data)-parity)//2)
        good=(a<nverts).astype(np.int32);c=np.r_[0,np.cumsum(good)]
        for pos in np.flatnonzero(c[nidx:]-c[:-nidx]==nidx):
            off=parity+2*int(pos)
            if off%4:continue
            vals=a[pos:pos+nidx]
            tri=vals.reshape(-1,3)
            if np.any((tri[:,0]==tri[:,1])|(tri[:,0]==tri[:,2])|(tri[:,1]==tri[:,2])):continue
            if len(np.unique(vals))!=nverts:continue
            try:inspect_faces(vals.tolist(),nverts)
            except ValueError:continue
            yield off

def recurse(data, first, second, pos, groups, gap=MAX_GAP):
    i=len(groups)
    if i==len(first):
        yield groups
        return
    count=first[i]['record_count']; idx_count=second[i]['low16']
    for padding in range(0,gap+1,2):
        off=pos+padding
        if off%4 or off+idx_count*2>len(data):continue
        vals=np.frombuffer(data,dtype='<u2',count=idx_count,offset=off)
        if int(vals.max(initial=0))>=count or len(np.unique(vals))!=count:continue
        tris=vals.reshape(-1,3)
        if np.any((tris[:,0]==tris[:,1])|(tris[:,0]==tris[:,2])|(tris[:,1]==tris[:,0])|(tris[:,1]==tris[:,2])):continue
        try:_, stats=inspect_faces(vals.tolist(),count)
        except ValueError:continue
        yield from recurse(data,first,second,off+idx_count*2,groups+[(off,tris.copy(),stats)])

def recover(data):
    meta=parse(data)
    if not meta['structural_checks_passed']:raise ValueError(meta['issues'])
    first=meta['first_table'];second=meta['second_table']
    vbytes=sum(r['record_count']*r['low_byte_of_upper16'] for r in first)
    sols=[]
    for off in candidates_first(data,first[0]['record_count'],second[0]['low16']):
        vstart=off-vbytes
        if vstart<0 or vstart%4:continue
        vertices=[];cur=vstart;good=True
        for row in first:
            n=row['record_count'];stride=row['low_byte_of_upper16']
            if stride not in (16,20,24,28,32,36,40,44):good=False;break
            xyz=np.ndarray((n,3),dtype='<f4',buffer=data,offset=cur,strides=(stride,4)).copy().astype(np.float64)
            if not np.isfinite(xyz).all() or np.max(np.abs(xyz))>100 or not(.01 < np.ptp(xyz,axis=0).max()<5):good=False;break
            vertices.append(xyz);cur+=n*stride
        if not good:continue
        firstvals=np.frombuffer(data,dtype='<u2',count=second[0]['low16'],offset=off).reshape(-1,3)
        _,stats=inspect_faces(firstvals.ravel().tolist(),first[0]['record_count'])
        for tail in recurse(data,first,second,off+second[0]['low16']*2,[(off,firstvals,stats)]):
            areas=[]
            for xyz,(_,tris,_) in zip(vertices,tail):
                pts=xyz[tris];ar=np.linalg.norm(np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]),axis=1)/2
                if not np.isfinite(ar).all() or np.min(ar)<=1e-9:break
                areas.append(float(ar.min()))
            if len(areas)==len(first):sols.append((vstart,vertices,tail,areas))
    if not sols:raise ValueError('No fully validated candidate')
    # In cases of a 12-byte index-stream shift, the earliest position represents the
    # earliest full-triangle sequence. Record ambiguity instead of silently claiming uniqueness.
    sols.sort(key=lambda v:v[2][0][0]);return sols
