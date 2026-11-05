"""Owner-authored long/short Move Dex data; no original game values."""
from pathlib import Path
import struct,sys
def stage(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    rows=[]
    for i in range(559):
        name=f'Synthetic Move {i:03d}'.encode()
        text=(b''.join(f'PAGE{n:02d}_'.encode()+bytes((65+n,))*21 for n in range(10))
              if i==0 else b'SHORT C360 DESCRIPTION')
        rows.append(struct.pack('<HHH',len(name),len(text),0)+name+text)
    offsets=[8+4*560]
    for row in rows:offsets.append(offsets[-1]+len(row))
    (root/'moves.p3dm').write_bytes(b'P3DM'+struct.pack('<HH',1,559)+struct.pack('<560I',*offsets)+b''.join(rows))
if __name__=='__main__':stage(sys.argv[1])
