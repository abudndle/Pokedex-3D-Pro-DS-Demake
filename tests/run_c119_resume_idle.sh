#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/resume_state.c source/title_idle.c \
  source/feature_menu.c source/dsi_features.c \
  tests/test_c119_resume_title_idle.c -o "$tmp/c119"
"$tmp/c119" "$tmp/pokedex"
