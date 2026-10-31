#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/Pokedex 3D Pro"
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/photo_album.c tests/test_photo_album_smoke.c -o "$tmp/test"
"$tmp/test" "$tmp/Pokedex 3D Pro/Photos"
