#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/full.p3dx" "$tmp/truncated.p3dx" <<'PY'
import struct,sys
header=struct.pack('<4sHH',b'P3DX',1,649)
with open(sys.argv[1],'wb') as f:
 f.write(header)
 for i in range(649):
  name={0:'Bulbasaur',24:'Pikachu',62:'Abra'}.get(i,'Species%d'%i)
  desc={0:'Seed Pokemon grows with sunlight',24:'Electric Pokemon'}.get(i,'Description %d'%i)
  def field(s,width):
   data=s.encode('ascii')
   assert len(data)<width
   return data.ljust(width,b'\0')
  f.write(field(name,32)+field(desc,192)+field('0.7m',16)+field('6.9kg',16))
with open(sys.argv[1],'rb') as f:
 data=f.read()
with open(sys.argv[2],'wb') as f:
 f.write(data[:-1])
PY
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
  source/dex_text.c source/dex_search.c source/records.c \
  source/feature_menu.c source/dsi_features.c \
  tests/test_c82_dex_search.c -o "$tmp/test"
"$tmp/test" "$tmp/full.p3dx" "$tmp/truncated.p3dx"
