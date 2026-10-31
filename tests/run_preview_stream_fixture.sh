#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/nitrofs/preview"
python3 - "$tmp/nitrofs/preview/p000.ds3m" <<'PY'
import struct, sys
with open(sys.argv[1], "wb") as f:
    f.write(struct.pack("<4sHHII",b"DS3M",1,1,0,42))
    f.write(struct.pack("<9h",*range(9)))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST -Itools/host_stub -Isource source/preview_stream.c tests/test_preview_stream_fixture.c -o "$tmp/test_preview"
(cd "$tmp" && ./test_preview)
