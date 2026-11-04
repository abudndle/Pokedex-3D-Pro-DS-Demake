"""Owner-independent transport fixtures; never original Pokemon data."""
from pathlib import Path
import struct
import sys
import zlib


def stage(root):
    root=Path(root);(root/'details').mkdir(parents=True,exist_ok=True)
    (root/'data').mkdir(exist_ok=True)
    for species,targets in ((0,(4,648)),(4,())):
        b=bytearray(64);b[:6]=b'P3SD\x01\x04'
        struct.pack_into('<H',b,6,species);b[11]=len(targets)
        for i,target in enumerate(targets):struct.pack_into('<H',b,26+2*i,target)
        struct.pack_into('<I',b,60,zlib.crc32(b[:60]))
        (root/'details'/f's{species:03d}-f000.p3sd').write_bytes(b)
    text=bytearray(b'P3DX\x01\0'+struct.pack('<H',649))
    for species in range(649):
        b=bytearray(256);name=f'Synthetic {species:03d}'.encode('ascii')
        b[:len(name)]=name;text.extend(b)
    (root/'data'/'dex_en.p3dx').write_bytes(text)


if __name__=='__main__':stage(sys.argv[1])
