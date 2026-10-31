#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/dex.p3dx" <<'PYFIXTURE'
import struct,sys
with open(sys.argv[1],'wb') as f:
    f.write(struct.pack('<4sHH',b'P3DX',1,649))
    for i in range(649):
        name={0:b'Synthetic entry',648:b'Last entry'}.get(i,b'')
        description=(b'0123456789'*20)[:191] if i==0 else b''
        f.write(name.ljust(32,b'\0')+description.ljust(192,b'\0')+
                (b'1.2m' if i==0 else b'').ljust(16,b'\0')+
                (b'3.4kg' if i==0 else b'').ljust(16,b'\0'))
PYFIXTURE
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/dex_info.c source/dex_text.c tests/test_dex_info.c -o "$tmp/test"
"$tmp/test" "$tmp/dex.p3dx"
