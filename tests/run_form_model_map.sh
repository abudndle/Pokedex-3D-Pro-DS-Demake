#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3fm" "$tmp/invalid.p3fm" <<'PY'
import struct,sys
def write(path,records):
 with open(path,"wb") as f:
  f.write(struct.pack("<4sHH",b"P3FM",1,len(records)))
  for row in records:f.write(struct.pack("<3H",*row))
write(sys.argv[1],[(0,1,737),(0,2,7),(648,1,400)])
write(sys.argv[2],[(0,2,7),(0,1,737)]) # unsorted
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/form_model_map.c tests/test_form_model_map.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3fm" "$tmp/invalid.p3fm"
