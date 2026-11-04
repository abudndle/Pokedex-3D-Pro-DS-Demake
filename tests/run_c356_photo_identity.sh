#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/Pokedex/Photos"
python3 tests/c355_png_fixtures.py "$tmp/Pokedex/Photos"
cc -std=c11 -O2 -Wall -Wextra -Werror ${P3D_HOST_SANITIZERS:-} -Isource source/photo_album.c source/photo_png.c source/photo_viewer.c tests/c356_photo_identity.c -o "$tmp/identity"
"$tmp/identity" "$tmp/Pokedex/Photos"
