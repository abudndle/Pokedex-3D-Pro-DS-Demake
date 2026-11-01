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
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST -Itools/host_stub -Isource source/preview_stream.c source/preview_chunk_stream.c source/model_uv.c tests/test_preview_stream_fixture.c -o "$tmp/test_preview"
(cd "$tmp" && ./test_preview)
