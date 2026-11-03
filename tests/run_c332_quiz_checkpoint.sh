#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/challenge.c source/resume_state.c source/feature_menu.c source/dsi_features.c \
 tests/c332_quiz_checkpoint.c -o "$tmp/test"
for stage in first check-first review check-review corrupt check-fallback; do
 "$tmp/test" "$stage" "$tmp/pokedex"
done
echo 'C332: exact active question/review, score and seed; cross-process dual-slot recovery: PASS'
