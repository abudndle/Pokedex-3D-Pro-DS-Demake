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
for stage in write-last verify-last write-last-review verify-last-review finish verify-finish; do
 "$tmp/test" "$stage" "$tmp/final"
done
for stage in text-question text-answer text-review; do
 "$tmp/test" "$stage" "$tmp/text"
done
echo 'C332: cross-process question/review, text clue page, ten-question finalization, and torn-slot recovery: PASS'
