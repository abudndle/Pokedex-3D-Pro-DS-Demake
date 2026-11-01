#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
from pathlib import Path
import struct
import sys
import zlib

root=Path(sys.argv[1])
# P3MT candidate, all triangle ranges contiguous and in-bounds.
ranges=[(0,1,10,2),(1,2,10,2),(3,1,12,7)]
(root/"test.p3mt").write_bytes(
    struct.pack("<4sHH",b"P3MT",1,len(ranges))+
    b"".join(struct.pack("<4H",*r) for r in ranges))
# Third texture 8 is valid but NOT referenced by the C5 source material.
entries=[(2,8,8,1),(7,16,8,1),(8,8,8,1)]
(root/"test.p3tx").write_bytes(
    struct.pack("<4sHH",b"P3TX",1,len(entries))+
    b"".join(struct.pack("<4H",*entry) for entry in entries))
# P3MR sidecar: mesh 25, four source triangles. C5 original primary draw
# material 10 uses slots 2/7 for three faces; material 12 uses slot 7.
source=[(0,3,10,2,7,0x0c02),(3,1,12,7,65535,0x0c02)]
body=b"".join(struct.pack("<6H",*r) for r in source)
header=struct.pack("<4s4HI",b"P3MR",1,25,4,len(source),zlib.crc32(body))
good=header+body
(root/"good.p3mr").write_bytes(good)
bad=bytearray(good);bad[-1]^=1
(root/"badcrc.p3mr").write_bytes(bad)
(root/"short.p3mr").write_bytes(good[:-1])
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
    source/model_materials.c source/model_textures.c \
    source/model_material_texture.c source/source_material_map.c \
    source/source_material_texture_match.c \
    tests/test_c109_original_material_refs.c -o "$tmp/c109"
"$tmp/c109" "$tmp/test.p3mt" "$tmp/test.p3tx" \
    "$tmp/good.p3mr" "$tmp/badcrc.p3mr" "$tmp/short.p3mr"
