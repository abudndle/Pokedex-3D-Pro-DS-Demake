#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/image.bmp" <<'PY'
import struct,sys
# Bottom-up BMP, 2x2, 24-bit, padded rows
pixel_rows=bytes([255,0,0,255,255,255,0,0, 0,0,255,0,255,0,0,0])
hdr=struct.pack('<2sIHHI',b'BM',54+len(pixel_rows),0,0,54)
dib=struct.pack('<IiiHHIIiiII',40,2,2,1,24,0,len(pixel_rows),0,0,0,0)
open(sys.argv[1],'wb').write(hdr+dib+pixel_rows)
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/bmp_loader.c tests/test_bmp_loader.c -o "$tmp/test"
"$tmp/test" "$tmp/image.bmp"
