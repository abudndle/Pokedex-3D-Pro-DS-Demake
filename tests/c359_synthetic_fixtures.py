"""Synthetic indexed C5 geometry fixtures: no original game data."""
import struct
import zipfile
from c358_synthetic_fixtures import fake_c5,NAMES

def source(key):
    d=bytearray(fake_c5(key))
    p=struct.unpack_from('<I',d,0x68)[0]
    end=p+struct.unpack_from('<I',d,p+4)[0]
    a,b,c,e=struct.unpack_from('<4I',d,p+0x3c)
    count=(b-a)//20
    if key=='gui_title':
        vc=[4,4,4,316,60,4];tc=[2,2,2,214,86,2];fmt=0x7520
    elif key=='gui_common':
        vc=[4]*5;tc=[2]*5;fmt=0x4420
    elif key=='en/gui_title':
        vc=[4,4,4,8,4,4,4,4];tc=[2,2,2,4,2,2,2,2];fmt=0x4420
    elif key=='jp/gui_title':
        vc=[4]*8;tc=[2]*8;fmt=0x4420
    else:
        vc=[152,4];tc=[76,2];fmt=0x4420
    assert len(vc)==len(tc)==count
    vertices=bytearray()
    triangles=bytearray()
    mesh=struct.unpack_from('<I',d,p+0x44)[0]
    for i,(n,t) in enumerate(zip(vc,tc)):
        voff=len(vertices)
        for j in range(n):
            tail=(struct.pack('<HH',(j%4)*512,(j%3)*512) if fmt==0x4420
                  else bytes((3,7,11,255)))
            vertices.extend(struct.pack('<fff',float((j%4)*8),
                                       float(-16+(j%3)*8),0.0)+tail)
        struct.pack_into('<5I',d,p+a+i*20,voff,0,0x02100000|n,fmt,0)
        struct.pack_into('<I',d,p+mesh+i*40+8,t)
        ids=[value for k in range(t) for value in
             ((0,1,2) if k%2==0 else (0,2,3))]
        triangles.extend(struct.pack('<'+'H'*len(ids),*ids))
        struct.pack_into('<IIHH',d,p+c+i*12,len(vertices)+
                         0,0,len(ids),2) # corrected below after all vertices
    offset=len(vertices)
    for i,t in enumerate(tc):
        struct.pack_into('<I',d,p+c+i*12,offset)
        offset+=t*6
    geom=bytes(vertices+triangles)
    struct.pack_into('<I',d,p+8,len(geom))
    struct.pack_into('<I',d,4,struct.unpack_from('<I',d,4)[0]+120+len(geom))
    return bytes(d[:end])+bytes(120)+geom+bytes(d[end:])

def archive(path):
    with zipfile.ZipFile(path,'w') as z:
        for key in NAMES:
            z.writestr('decoded_c5/gui/'+key+'.c5',source(key))
