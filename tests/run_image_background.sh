#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/image.bmp" <<'PY'
import struct,sys
rows=bytes([255,0,0,255,255,255,0,0, 0,0,255,0,255,0,0,0])
hdr=struct.pack('<2sIHHI',b'BM',54+len(rows),0,0,54)
dib=struct.pack('<IiiHHIIiiII',40,2,2,1,24,0,len(rows),0,0,0,0)
open(sys.argv[1],'wb').write(hdr+dib+rows)
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/custom_images.c source/bmp_loader.c source/image_background.c tests/test_image_background.c -o "$tmp/test"
"$tmp/test" "$tmp"
