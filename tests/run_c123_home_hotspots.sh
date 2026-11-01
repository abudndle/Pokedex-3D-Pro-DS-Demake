#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
import struct,sys,zlib
from pathlib import Path
root=Path(sys.argv[1])
entries=[(1,8,8,65,43),(3,75,8,132,43),(6,142,8,199,43),
         (10,8,60,65,95),(8,75,60,132,95),(9,142,60,199,95),
         (7,8,112,65,147)]
def make(items):
    body=b"".join(struct.pack("<5H",*item) for item in items)
    return struct.pack("<4sHHII",b"P3HM",1,7,0,zlib.crc32(body))+body
good=make(entries)
(root/"valid.p3hm").write_bytes(good)
(root/"truncated.p3hm").write_bytes(good[:-1])
(root/"trailing.p3hm").write_bytes(good+b"\0")
(root/"badcrc.p3hm").write_bytes(good[:-1]+bytes([good[-1]^1]))
def changed(name,idx,row):
    values=list(entries)
    values[idx]=row
    (root/name).write_bytes(make(values))
changed("duplicate.p3hm",1,(1,75,8,132,43))
changed("overlap.p3hm",1,(3,55,12,132,43))
changed("outside.p3hm",3,(10,8,175,65,193))
changed("unknown.p3hm",2,(5,142,8,199,43))
changed("thin.p3hm",2,(6,142,8,145,43))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/original_home_hotspots.c tests/test_c123_home_hotspots.c -o "$tmp/test"
"$tmp/test" "$tmp"
