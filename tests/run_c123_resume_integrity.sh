#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/resume_state.c source/feature_menu.c source/dsi_features.c \
  tests/test_c123_resume_integrity.c -o "$tmp/c123"
"$tmp/c123" "$tmp/pokedex"
