#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/animation_playback.c tests/test_c230_playback_controls.c -o "$tmp/test"
"$tmp/test"
