#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/all" "$tmp/one"
python3 - "$tmp/all" "$tmp/one" <<'PY'
import pathlib,struct,sys
a,b=map(pathlib.Path,sys.argv[1:])
for ident in (11,12):
 data=struct.pack("<4sHHH",b"P3PX",1,8,8)+struct.pack("<64H",*[0x7fff]*64)
 (a/f"t{ident:03d}.p3px").write_bytes(data)
 (b/"t011.p3px").write_bytes(data) if ident==11 else None
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST -Isource \
 source/model_textures.c source/model_material_texture.c \
 source/texture_pixels.c source/texture_asset.c \
 source/ds_texture_upload.c source/preview_texture_set.c \
 tests/test_preview_texture_set.c -o "$tmp/test"
"$tmp/test" "$tmp/all" "$tmp/one"
