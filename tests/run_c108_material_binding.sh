#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
from pathlib import Path
import struct
import sys
root=Path(sys.argv[1])
(root/"good").mkdir()
(root/"corrupt").mkdir()
# Four synthetic triangles. Three original-style material ranges:
# two consecutive ranges share texture 2, final range uses texture 7.
ranges=((0,1,10,2),(1,2,11,2),(3,1,12,7))
(root/"model.p3mt").write_bytes(
    struct.pack("<4sHH",b"P3MT",1,len(ranges))+
    b"".join(struct.pack("<4H",*r) for r in ranges))
textures=((2,8,8,1),(7,16,8,1))
(root/"model.p3tx").write_bytes(
    struct.pack("<4sHH",b"P3TX",1,len(textures))+
    b"".join(struct.pack("<4H",*t) for t in textures))
(root/"model.p3uv").write_bytes(
    struct.pack("<4sHH",b"P3UV",1,4)+
    struct.pack("<24h",*([0,0,4096,0,0,4096]*4)))
def pixels(version,w,h):
    return (struct.pack("<4sHHH",b"P3PX",version,w,h)+
            struct.pack("<%dH"%(w*h),*([0x9234]*(w*h))))
a=pixels(2,8,8)
b=pixels(1,16,8)
(root/"good/t002.p3px").write_bytes(a)
(root/"good/t007.p3px").write_bytes(b)
(root/"corrupt/t002.p3px").write_bytes(a)
(root/"corrupt/t007.p3px").write_bytes(b[:-2])
PY
cc -std=c11 -Wall -Wextra -Werror -O2 \
    -Itests/host_gl_stub -Isource \
    source/model_materials.c source/model_textures.c \
    source/model_material_texture.c source/model_uv.c \
    source/texture_pixels.c source/texture_asset.c \
    source/ds_texture_upload.c source/preview_texture_set.c \
    tests/test_c108_material_binding.c -o "$tmp/c108"
"$tmp/c108" "$tmp/model.p3mt" "$tmp/model.p3tx" "$tmp/model.p3uv" \
    "$tmp/good" "$tmp/corrupt"
