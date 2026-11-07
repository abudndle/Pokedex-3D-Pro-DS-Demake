#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror ${P3D_HOST_SANITIZERS:-} -Isource \
 source/resume_state.c source/feature_menu.c source/dsi_features.c \
 tests/c403_description_resume.c -o "$tmp/c403-resume"
for phase in write verify corrupt fallback close; do
 "$tmp/c403-resume" "$phase" "$tmp/pokedex"
done
