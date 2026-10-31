#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/materials.p3mt" "$tmp/valid.p3tx" "$tmp/missing.p3tx" <<'PY'
import struct,sys
with open(sys.argv[1],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3MT",1,2))
 f.write(struct.pack("<4H",0,2,5,12))
 f.write(struct.pack("<4H",2,1,9,13))
for path,ids in [(sys.argv[2],[12,13]),(sys.argv[3],[12])]:
 with open(path,"wb") as f:
  f.write(struct.pack("<4sHH",b"P3TX",1,len(ids)))
  for tid in ids:f.write(struct.pack("<4H",tid,8,8,1))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/model_materials.c source/model_textures.c source/model_material_texture.c tests/test_model_material_texture.c -o "$tmp/test"
"$tmp/test" "$tmp/materials.p3mt" "$tmp/valid.p3tx" "$tmp/missing.p3tx"
