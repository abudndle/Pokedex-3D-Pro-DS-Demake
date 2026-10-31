#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/animations"
python3 - "$tmp/animations" <<'PY'
from pathlib import Path
import struct,sys
root=Path(sys.argv[1])
def clip(name,version,yaw):
    data=struct.pack("<4sHH",b"P3AN",version,2)
    data+=struct.pack("<hhhH",yaw,0,0,2)
    data+=struct.pack("<hhhH",yaw+10,0,0,2)
    (root/name).write_bytes(data)
clip("p005.p3an",1,1)
clip("p005_a00.p3an",2,20)
clip("p005_a02.p3an",1,40)
clip("p006_a00.p3an",2,50)
(root/"p005_a01.p3an").write_bytes(b"invalid")
(root/"p007.p3an").write_bytes(b"invalid")
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/model_animation.c source/model_animation_library.c \
 tests/test_model_animation_library.c -o "$tmp/test"
"$tmp/test" "$tmp/animations"
