#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PYFIXTURE'
from pathlib import Path
import struct,sys
root=Path(sys.argv[1])
for variant in ('valid','missing_names','missing_descriptions'):
    with (root/(variant+'.p3dx')).open('wb') as f:
        f.write(struct.pack('<4sHH',b'P3DX',1,649))
        for i in range(649):
            name=b'' if variant=='missing_names' else ('Synthetic %03d'%i).encode()
            clue=b'' if variant=='missing_descriptions' else b'S'*180
            f.write(name.ljust(32,b'\0')+clue.ljust(192,b'\0')+b'\0'*32)
PYFIXTURE
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/challenge.c source/challenge_text.c source/dex_text.c \
 tests/test_c331_challenge_text.c -o "$tmp/test"
"$tmp/test" "$tmp/valid.p3dx" "$tmp/missing_names.p3dx" "$tmp/missing_descriptions.p3dx"
