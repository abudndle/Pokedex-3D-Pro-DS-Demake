#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -Isource source/animation_playback.c tests/test_animation_playback.c -o "$tmp"
"$tmp"
