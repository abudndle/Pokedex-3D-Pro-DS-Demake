#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/Photos" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0,'tests')
from c355_album_view_gate import synthetic_photo
root=Path(sys.argv[1]);root.mkdir()
for n in range(1,10):(root/f'AR_{n:04d}.png').write_bytes(synthetic_photo(n))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror ${P3D_HOST_SANITIZERS:-} -Isource source/photo_album.c source/photo_png.c source/photo_viewer.c tests/c357_slideshow.c -o "$tmp/slideshow"
"$tmp/slideshow" "$tmp/Photos"
python3 - "$tmp/Photos" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0,'tests')
from c355_album_view_gate import synthetic_photo
root=Path(sys.argv[1])
for n in range(1,10):
    assert (root/f'AR_{n:04d}.png').read_bytes() == (b'invalid' if n==8 else synthetic_photo(n))
print('C357 only deliberately corrupted fixture changed; slideshow media read-only: PASS')
PY
