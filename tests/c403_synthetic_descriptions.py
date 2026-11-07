"""Authored description transport, never original game content."""
from pathlib import Path
import struct,sys

def description(species,changed=False):
    if species==0:
        prefix='NEXT' if changed else 'PAGE'
        text=' '.join(f'{prefix}{i//4+1}_ROW{i%4+1}_AAAA' for i in range(12))
        assert len(text)==191
        return text
    return 'SHORT SOURCE DESCRIPTION' if species==1 else ''

def stage(root,changed=False):
    root=Path(root);(root/'data').mkdir(parents=True,exist_ok=True)
    data=bytearray(b'P3DX\x01\0'+struct.pack('<H',649))
    for species in range(649):
        row=bytearray(256);name=f'SYNTHETIC {species:03d}'.encode()
        text=description(species,changed).encode();row[:len(name)]=name;row[32:32+len(text)]=text;data.extend(row)
    (root/'data/dex_en.p3dx').write_bytes(data)
if __name__=='__main__':stage(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='changed')
