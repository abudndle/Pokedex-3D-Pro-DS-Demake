#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/valid.p3sm" "$tmp/invalid.p3sm" <<'PY'
import struct,sys
ids=[0xffff]*649
ids[0]=737
ids[648]=0
with open(sys.argv[1],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3SM",1,649))
 f.write(struct.pack("<649H",*ids))
ids[0]=738
with open(sys.argv[2],"wb") as f:
 f.write(struct.pack("<4sHH",b"P3SM",1,649))
 f.write(struct.pack("<649H",*ids))
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/species_model_map.c tests/test_species_model_map.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3sm" "$tmp/invalid.p3sm"
