#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
  source/dsi_camera_session.c source/dsi_camera_preview.c \
  tests/c338_dsi_camera_preview.c -o "$tmp/test"
"$tmp/test"
