#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/meta.p3tx" "$tmp/good.p3px" "$tmp/bad.p3px" <<'PY'
import struct,sys
open(sys.argv[1],"wb").write(struct.pack("<4sHH4H",b"P3TX",1,1,3,8,8,1))
open(sys.argv[2],"wb").write(struct.pack("<4sHHH",b"P3PX",1,8,8)+bytes(128))
open(sys.argv[3],"wb").write(struct.pack("<4sHHH",b"P3PX",1,16,8)+bytes(256))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/model_textures.c source/texture_pixels.c source/texture_asset.c tests/test_texture_asset.c -o "$tmp/test"
"$tmp/test" "$tmp/meta.p3tx" "$tmp/good.p3px" "$tmp/bad.p3px"
