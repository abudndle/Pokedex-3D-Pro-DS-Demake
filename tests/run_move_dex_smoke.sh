#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/moves.p3dm" <<'PY'
import struct,sys
rows=[]
for i in range(559):
    name=b'Pound' if i==0 else (b'Punch' if i==1 else b'Move')
    desc=b'Fixture only';effect=b'No original assets'
    rows.append(struct.pack('<HHH',len(name),len(desc),len(effect))+name+desc+effect)
base=8+4*560;offsets=[base]
for r in rows:offsets.append(offsets[-1]+len(r))
with open(sys.argv[1],'wb') as f:
    f.write(b'P3DM'+struct.pack('<HH',1,559))
    f.write(struct.pack('<560I',*offsets))
    for r in rows:f.write(r)
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/move_dex.c tests/test_move_dex_smoke.c -o "$tmp/test"
"$tmp/test" "$tmp/moves.p3dm"
