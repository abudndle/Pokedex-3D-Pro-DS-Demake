#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3an" "$tmp/invalid.p3an" <<'PY'
import struct,sys
with open(sys.argv[1],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3AN",1,2))
 f.write(struct.pack("<hhhH",0,0,0,2))
 f.write(struct.pack("<hhhH",64,0,0,3))
with open(sys.argv[2],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3AN",1,1))
 f.write(struct.pack("<hhhH",0,0,0,0))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/model_animation.c tests/test_model_animation.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3an" "$tmp/invalid.p3an"
