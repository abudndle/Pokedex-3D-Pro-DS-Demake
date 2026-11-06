"""Authored text transport fixture, never original game names."""
from pathlib import Path
import struct,sys
root=Path(sys.argv[1]);(root/'data').mkdir(parents=True,exist_ok=True)
b=bytearray(b'P3DX\x01\0'+struct.pack('<H',649))
for i in range(649):
    row=bytearray(256);name=f'SYNTHETIC ENTRY {i:03d}'.encode();row[:len(name)]=name;b.extend(row)
(root/'data/dex_en.p3dx').write_bytes(b)
