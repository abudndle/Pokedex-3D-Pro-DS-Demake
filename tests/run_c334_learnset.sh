#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/learnset.c tests/c334_learnset.c -o "$tmp/c334"
"$tmp/c334" "$tmp/learnset.p3sl"
