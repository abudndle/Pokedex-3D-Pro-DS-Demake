#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/good.p3uv" "$tmp/bad.p3uv" <<'PY'
import struct,sys
header=struct.pack("<4sHH",b"P3UV",1,2)
uv=[4096,0,4096,4096,0,4096,0,0,0,4096,4096,-2048]
open(sys.argv[1],"wb").write(header+struct.pack("<12h",*uv))
open(sys.argv[2],"wb").write(header+struct.pack("<11h",*uv[:11]))
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/model_uv.c tests/test_model_uv.c -o "$tmp/test"
"$tmp/test" "$tmp/good.p3uv" "$tmp/bad.p3uv"
