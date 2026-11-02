#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
import pathlib,struct,sys
root=pathlib.Path(sys.argv[1]);header=lambda n:struct.pack('<4sHH',b'P3UV',1,n)
uv=[4096,0,4096,4096,0,4096,0,0,0,4096,4096,-2048]
good=header(2)+struct.pack('<12h',*uv)
(root/'good.p3uv').write_bytes(good)
(root/'short.p3uv').write_bytes(good[:-1])
(root/'trailing.p3uv').write_bytes(good+b'!')
(root/'magic.p3uv').write_bytes(b'BAD!'+good[4:])
(root/'version.p3uv').write_bytes(good[:4]+struct.pack('<H',2)+good[6:])
large=[-32768]+[0]*3598+[32767]
(root/'large.p3uv').write_bytes(header(600)+struct.pack('<3600h',*large))
(root/'count.p3uv').write_bytes(header(1)+struct.pack('<6h',*uv[:6]))
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/model_uv.c tests/test_model_uv.c -o "$tmp/test"
"$tmp/test" "$tmp/good.p3uv" "$tmp/short.p3uv" "$tmp/trailing.p3uv" "$tmp/magic.p3uv" "$tmp/version.p3uv" "$tmp/large.p3uv" "$tmp/count.p3uv"
