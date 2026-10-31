#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3an" "$tmp/invalid.p3an" "$tmp/truncated.p3an" "$tmp/trailing.p3an" "$tmp/interpolated.p3an" <<'PY'
import struct,sys
with open(sys.argv[1],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3AN",1,2))
 f.write(struct.pack("<hhhH",0,0,0,2))
 f.write(struct.pack("<hhhH",64,0,0,3))
with open(sys.argv[2],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3AN",1,1))
 f.write(struct.pack("<hhhH",0,0,0,0))
with open(sys.argv[3],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3AN",1,1))
 f.write(bytes(7))
with open(sys.argv[4],"wb") as f:
 f.write(struct.pack("<4sHHhhhHB",b"P3AN",1,1,0,0,0,1,42))
with open(sys.argv[5],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3AN",2,2))
 f.write(struct.pack("<hhhH",32760,16000,0,4))
 f.write(struct.pack("<hhhH",8,-16000,64,4))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/model_animation.c tests/test_model_animation.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3an" "$tmp/invalid.p3an" "$tmp/truncated.p3an" "$tmp/trailing.p3an" "$tmp/interpolated.p3an"
