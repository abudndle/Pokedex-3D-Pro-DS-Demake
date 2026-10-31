#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3mt" "$tmp/invalid.p3mt" <<'PY'
import struct,sys
def write(path,rows):
 with open(path,"wb") as f:
  f.write(struct.pack("<4sHH",b"P3MT",1,len(rows)))
  for row in rows:f.write(struct.pack("<4H",*row))
write(sys.argv[1],[(0,2,5,12),(2,1,9,13)])
write(sys.argv[2],[(0,2,5,12),(1,1,9,13)]) # overlapping range
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/model_materials.c tests/test_model_materials.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3mt" "$tmp/invalid.p3mt"
