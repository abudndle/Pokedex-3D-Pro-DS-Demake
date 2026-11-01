#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
import pathlib,struct,sys
root=pathlib.Path(sys.argv[1])
pixels=struct.pack("<64H",0x1234,0x9234,*([0x8000]*62))
for version in (1,2):
    (root/f"texture_{version}.p3px").write_bytes(
        struct.pack("<4sHHH",b"P3PX",version,8,8)+pixels)
PY
cc -std=c11 -Wall -Wextra -Werror -O2 \
   -Itests/host_gl_stub -Isource \
   source/texture_pixels.c source/ds_texture_upload.c \
   tests/test_c107_native_texture_alpha.c -o "$tmp/c107"
"$tmp/c107" "$tmp/texture_1.p3px" "$tmp/texture_2.p3px"
