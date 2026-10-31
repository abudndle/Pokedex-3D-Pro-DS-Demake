#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PYFIXTURE'
from pathlib import Path
import struct,sys
root=Path(sys.argv[1])
header=struct.pack('<4sHH',b'P3DX',1,649)
records=[]
for i in range(649):
    name={0:'Alpha',1:'Alder',2:'Beta',648:'Apex'}.get(i,'').encode()
    records.append(b'X'*256 if i==3 else name.ljust(32,b'\0')+b'\0'*224)
valid=header+b''.join(records)
(root/'valid.p3dx').write_bytes(valid)
for name,data in {'truncated':valid[:-1],'trailing':valid+b'x','header':header,
                  'version':valid[:4]+b'\2\0'+valid[6:],
                  'count':valid[:6]+b'\1\0'+valid[8:],
                  'magic':b'FAIL'+valid[4:]}.items():
    (root/(name+'.p3dx')).write_bytes(data)
PYFIXTURE
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/name_search.c source/dex_search.c source/dex_text.c tests/test_name_search.c -o "$tmp/test"
for malformed in truncated trailing header version count magic; do
    "$tmp/test" "$tmp/valid.p3dx" "$tmp/$malformed.p3dx"
done
