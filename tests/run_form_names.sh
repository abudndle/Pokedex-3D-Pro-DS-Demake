#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3fn" "$tmp/bad.p3fn" <<'PY'
import struct,sys
header=struct.pack("<4sHH",b"P3FN",1,1)
with open(sys.argv[1],"wb") as f:
 f.write(header)
 f.write(struct.pack("<HH24s",0,1,b"Test Form"))
with open(sys.argv[2],"wb") as f:
 f.write(header)
 f.write(struct.pack("<HH24s",0,1,b"A"*24)) # nonterminated
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/form_names.c tests/test_form_names.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3fn" "$tmp/bad.p3fn"
