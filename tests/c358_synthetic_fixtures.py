"""Completely synthetic C5 source fixtures for C358 tests; no Nintendo bytes."""
import struct
import warnings
import zipfile

NAMES=('gui_title','gui_common','en/gui_title',
       *(f'en/gui{i:02d}' for i in range(1,7)),
       'jp/gui_title',*(f'jp/gui{i:02d}' for i in range(1,7)))

def fake_c5(key, *, problem=None):
    if key=='gui_title':
        tex,mat,nodes,draws=1,2,16,6
        texrefs=[65535,65535]
        draw_mat=[0,0,0,0,1,0]
        draw_nodes=[1,4,7,8,9,12]
    elif key=='gui_common':
        tex,mat,nodes,draws=5,5,5,5
        texrefs=[0,1,2,3,4]
        draw_mat=[3,0,1,4,2]
        draw_nodes=[0,1,2,3,4]
    elif key.endswith('/gui_title'):
        tex,mat,nodes,draws=1,8,11 if key.startswith('en/') else 10,8
        texrefs=[0]*8
        draw_mat=[2,0,3,4,5,1,7,6] if key.startswith('en/') else [3,4,5,6,1,2,0,7]
        draw_nodes=[1,2,3,4,5,6,7,10] if key.startswith('en/') else [1,2,3,4,4,5,6,9]
    else:
        tex=11 if int(key[-2:]) in (3,6) else 10
        mat,nodes,draws=1,3,2
        texrefs=[0]
        draw_mat=[0,0]
        draw_nodes=[1,2]
    if problem=='texture': texrefs[0]=tex
    if problem=='changed_material': texrefs[0]=1
    names=bytearray()
    tex_table=bytearray(tex*28)
    for i in range(tex):
        struct.pack_into('<7I',tex_table,i*28,i*256,0,len(names),
                         256,0x00080008,0x14016752,0x10001)
        names.extend(f'atlas_{i}\0'.encode())
    p=(120+len(tex_table)+len(names)+3)//4*4
    mat_start=120
    node_start=mat_start+mat*52
    vertex_start=node_start+nodes*56
    index_start=vertex_start+draws*20
    mesh_start=index_start+draws*12
    end=mesh_start+draws*40
    inner=bytearray(end)
    inner[:4]=b'\xc5\x78\x00\x02'
    struct.pack_into('<I',inner,4,end)
    struct.pack_into('<HH',inner,0x10,mat,nodes)
    struct.pack_into('<HH',inner,0x14,draws,draws)
    for off,val in ((0x34,mat_start),(0x38,node_start),(0x3c,vertex_start),
                    (0x40,index_start),(0x44,mesh_start),(0x48,end),
                    (0x50,end),(0x64,end)):
        struct.pack_into('<I',inner,off,val)
    for i,t in enumerate(texrefs):
        struct.pack_into('<H',inner,mat_start+i*52+2,t)
    for i in range(nodes):
        struct.pack_into('<12f',inner,node_start+i*56,
            1,0,0,float(i*10),0,1,0,float(-i),0,0,1,0)
    for i in range(draws):
        m=draw_mat[i]
        n=draw_nodes[i]
        b=i
        primitive=2
        max_x=32
        if i==0:
            if problem=='material':m=mat
            if problem=='node':n=nodes
            if problem=='buffer':b=draws
            if problem=='primitive':primitive=0
            if problem=='bounds':max_x=-1
        struct.pack_into('<4HII6f',inner,mesh_start+i*40,
            m,i,b,n,primitive,0x0c030000,0,-16,0,max_x,0,0)
    root=bytearray(p)
    root[:4]=b'\xc5\x78\x00\x01'
    struct.pack_into('<I',root,0x0c,tex<<16)
    struct.pack_into('<I',root,0x58,120)
    struct.pack_into('<I',root,0x5c,120+len(tex_table))
    struct.pack_into('<I',root,0x64,120+len(tex_table))
    struct.pack_into('<I',root,0x68,p)
    root[120:120+len(tex_table)]=tex_table
    root[120+len(tex_table):120+len(tex_table)+len(names)]=names
    root.extend(inner)
    struct.pack_into('<II',root,4,len(root)-120,tex*256)
    root.extend(bytes((1,32,48,255))*64*tex)
    return bytes(root)

def fake_archive(path, *, mismatch=False, omit=None, duplicate=False):
    with zipfile.ZipFile(path,'w') as z:
        for key in NAMES:
            name=f'decoded_c5/gui/{key}.c5'
            if name!=omit:
                z.writestr(name,fake_c5(key,problem='changed_material'
                      if mismatch and key=='jp/gui01' else None))
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                z.writestr('decoded_c5/gui/gui_title.c5',fake_c5('gui_title'))
