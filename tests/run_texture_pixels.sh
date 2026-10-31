#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3px" "$tmp/truncated.p3px" <<'PY'
import struct,sys
pixels=[0x7fff]+[0]*62+[0x001f]
header=struct.pack("<4sHHH",b"P3PX",1,8,8)
open(sys.argv[1],"wb").write(header+struct.pack("<64H",*pixels))
open(sys.argv[2],"wb").write(header+struct.pack("<63H",*pixels[:63]))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/texture_pixels.c tests/test_texture_pixels.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3px" "$tmp/truncated.p3px"
