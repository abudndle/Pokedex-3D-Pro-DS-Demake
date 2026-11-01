#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/nitrofs/preview"
python3 - "$tmp/nitrofs/preview/p000.ds3m" <<'PY'
import struct, sys
with open(sys.argv[1], "wb") as f:
    f.write(struct.pack("<4sHHII",b"DS3M",1,1,0,42))
    f.write(struct.pack("<9h",*range(9)))
    
for count in (600, 601):
    with open(sys.argv[1].replace("p000", "p001" if count == 600 else "p002"), "wb") as f:
        f.write(struct.pack("<4sHHII", b"DS3M", 1, count, 0, count))
        f.write(struct.pack("<9h", *range(9)) * count)
with open(sys.argv[1].replace("p000", "p003"), "wb") as f:
    f.write(struct.pack("<4sHHII", b"DS3M", 2, 2, 0, 42))
    f.write(struct.pack("<9h", *range(9)) * 2)
    f.write(bytes((255, 0, 0, 0, 255, 0)))
with open(sys.argv[1].replace("p000", "p004"), "wb") as f:
    f.write(struct.pack("<4sHHII", b"DS3M", 2, 2, 0, 42))
    f.write(struct.pack("<9h", *range(9)) * 2)
    f.write(bytes((255, 0, 0)))  # truncated colors must fail
with open(sys.argv[1].replace("p000.ds3m", "p000.p3uv"), "wb") as f:
    f.write(struct.pack("<4sHH",b"P3UV",1,1))
    f.write(struct.pack("<6h",0,0,4096,0,0,4096))
with open(sys.argv[1].replace("p000", "p737"), "wb") as f:
    f.write(struct.pack("<4sHHII", b"DS3M", 1, 1, 0, 1))
    f.write(struct.pack("<9h", *range(9)))
# C103: synthetic DS3M headers with corrupt reserved/source-count fields.
# These are not real Nintendo game assets.
for model_id, reserved, original_count in ((7, 1, 42), (8, 0, 0), (9, 0, 0x80000000)):
    target = sys.argv[1].replace("p000", f"p{model_id:03d}")
    with open(target, "wb") as f:
        f.write(struct.pack("<4sHHII", b"DS3M", 1, 1, reserved, original_count))
        f.write(struct.pack("<9h", *range(9)))
# Synthetic geometry-only three-chunk C96 source preview. No materials.
import zlib
triangle=struct.pack("<9h6h3B",*[0]*9,*[100]*6,192,224,232)
chunks=[triangle*600,triangle*600,triangle*2]
index=bytearray()
offset=24+16*len(chunks)
for k,block in enumerate(chunks):
    index+=struct.pack("<IHHII",k*600,len(block)//33,0,offset,zlib.crc32(block))
    offset+=len(block)
full=struct.pack("<4s4H3I",b"P3CS",1,5,3,0,1202,5000,zlib.crc32(index))+index+b"".join(chunks)
with open(sys.argv[1].replace("p000.ds3m","p005.p3cs"),"wb") as f:f.write(full)
with open(sys.argv[1].replace("p000.ds3m","p006.p3cs"),"wb") as f:f.write(full[:-1]+bytes([full[-1]^1]))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST -Itools/host_stub -Isource source/preview_stream.c source/preview_chunk_stream.c source/model_uv.c tests/test_preview_stream_fixture.c -o "$tmp/test_preview"
(cd "$tmp" && ./test_preview)
