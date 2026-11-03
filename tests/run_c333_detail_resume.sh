#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/resume_state.c source/feature_menu.c source/dsi_features.c \
  tests/c333_detail_resume.c -o "$tmp/c333-resume"
for stage in first second verify corrupt fallback close; do
 "$tmp/c333-resume" "$stage" "$tmp/pokedex"
done
