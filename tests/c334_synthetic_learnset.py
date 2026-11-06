"""Owner-independent transport fixture; never an original Pokemon learnset."""
import struct
import sys
import zlib
from pathlib import Path


def payload():
    header = struct.pack('<4sBBHHH', b'P3SL', 1, 1, 0, 0, 9)
    rows = b''.join(struct.pack('<HBBH', i, 1, i + 1, 0) for i in range(9))
    return header + struct.pack('<I', zlib.crc32(header + rows)) + rows


if __name__ == '__main__':
    root = Path(sys.argv[1]) / 'learnsets'
    root.mkdir(parents=True, exist_ok=True)
    (root / 's000-f000.p3sl').write_bytes(payload())
