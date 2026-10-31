#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/good.p3tx" "$tmp/bad.p3tx" <<'PY'
import struct,sys
def write(path,rows):
 with open(path,"wb") as f:
  f.write(struct.pack("<4sHH",b"P3TX",1,len(rows)))
  for row in rows:f.write(struct.pack("<4H",*row))
write(sys.argv[1],[(3,64,64,1),(8,128,128,1)])
write(sys.argv[2],[(3,64,64,1),(8,96,128,1)])
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/model_textures.c tests/test_model_textures.c -o "$tmp/test"
"$tmp/test" "$tmp/good.p3tx" "$tmp/bad.p3tx"
