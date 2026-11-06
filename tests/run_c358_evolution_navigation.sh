#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp/details.p3sd" <<'PY'
from pathlib import Path
import struct,sys,zlib
b=bytearray(64);b[:6]=b'P3SD\x01\x04';b[8]=2;b[11]=2
struct.pack_into('<HH',b,26,4,648)
struct.pack_into('<I',b,60,zlib.crc32(b[:60]))
Path(sys.argv[1]).write_bytes(b)
PY
cc -std=c11 -O2 -Wall -Wextra -Werror ${P3D_HOST_SANITIZERS:-} -Isource source/species_details.c source/resume_state.c source/feature_menu.c source/dsi_features.c tests/c358_evolution_navigation.c -o "$tmp/evolution"
"$tmp/evolution" "$tmp/details.p3sd" "$tmp/pokedex" write
"$tmp/evolution" "$tmp/details.p3sd" "$tmp/pokedex" verify
