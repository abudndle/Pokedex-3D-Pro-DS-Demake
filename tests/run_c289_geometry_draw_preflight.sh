#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -DC7_TEST_HOST -Isource \
  source/verified_primitive_stream.c source/verified_primitive_bridge.c \
  source/verified_primitive_draw.c tests/c289_geometry_draw_preflight.c \
  -o "$tmp/c289"
"$tmp/c289"
