#!/bin/sh
# Each invocation runs in a separate host process, using real native modules.
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/save_store.c source/resume_state.c source/game_save_bridge.c \
  source/feature_menu.c source/dsi_features.c \
  tests/c260_save_process_resume.c -o "$tmp/session"
base="$tmp/pokedex3d"
"$tmp/session" write-first "$base"
"$tmp/session" verify-first "$base"
"$tmp/session" write-second "$base"
"$tmp/session" verify-second "$base"
"$tmp/session" damage-newest "$base"
"$tmp/session" verify-first "$base"
"$tmp/session" write-second "$base"
"$tmp/session" verify-second "$base"
echo 'C260: cross-process P3SV/P3RV save, torn-slot fallback and recovery: PASS (host only)'
