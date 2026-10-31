#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/dex.bin" <<'PY'
import struct,sys
with open(sys.argv[1],'wb') as f:
    f.write(b'P3DX'+bytes((1,0))+struct.pack('<H',649))
    for i in range(649):
        name=({0:'Bulbasaur',1:'Ivysaur',2:'Venusaur',3:'Charmander'}.get(i,'Other')).encode()
        f.write(name.ljust(32,b'\0') + b'\0'*224)
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/dex_search.c source/dex_text.c tests/test_dex_search_smoke.c -o "$tmp/dex_test"
"$tmp/dex_test" "$tmp/dex.bin"
