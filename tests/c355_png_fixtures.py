"""Synthetic PNG transport fixtures; never original Pokemon or camera art."""
from pathlib import Path
import struct
import sys
import zlib


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def png(raw=b'\0\xff\0\0\0\0\xff', width=2, height=1, color=2,
        depth=8, interlace=0, compressed=None, before=b''):
    header = struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, interlace)
    compressed = zlib.compress(raw) if compressed is None else compressed
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + before
            + chunk(b'IDAT', compressed) + chunk(b'IEND', b''))


def fixtures(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    valid = png()
    bad_crc = bytearray(valid)
    bad_crc[-5] ^= 1
    values = {
        1: valid, 2: valid[:-1],
        3: png(b'\0\xff\0\0\x80\0\0\xff\0', color=6),
        4: bytes(bad_crc), 5: png(width=641), 6: valid+b'x',
        7: png(compressed=zlib.compress(b'\0\xff\0\0\0\0\xff')[:-4]),
        8: png(b'\0\xff\0\0\0\0\xff\0'),
        9: valid[:33]+chunk(b'IEND', b''),
        10: png(before=chunk(b'ABCD', b'unknown')),
        11: png(b'\5\xff\0\0\0\0\xff'),
        12: png(interlace=1),
        13: png((b'\0'+b'\0\xff\0'*640)*480, width=640, height=480),
        14: png(b'\1\xff\0\0\1\0\xff'),
        15: png(b'\0\x40', color=3, depth=1,
                before=chunk(b'PLTE', b'\xff\0\0\0\0\xff')+chunk(b'tRNS', b'\xff\x80')),
        16: png(compressed=zlib.compress(b'\0\xff\0\0\0\0\xff')+b'junk'),
        17: png(b'\0\xff\0\0'),
        18: png((b'\0'+b'\x7f'*255)*128, width=255, height=128, color=0,
                compressed=zlib.compress((b'\0'+b'\x7f'*255)*128)[:-4]),
        19: png(before=chunk(b'tRNS', b'\0\xff\0\0\0\0')),
        20: png(before=chunk(b'teXt', b'x'*(2*1024*1024))),
        21: png(before=chunk(b'teXt', b'Comment\0Synthetic only')),
        22: valid[:33]+chunk(b'IDAT', b'')+valid[33:-12]+chunk(b'IDAT', b'')+valid[-12:],
    }
    for ident, data in values.items():
        (root/f'AR_{ident:04d}.png').write_bytes(data)


if __name__ == '__main__':
    fixtures(sys.argv[1])
