#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST -Isource \
 source/verified_vertex_stream.c source/verified_primitive_stream.c \
 source/verified_primitive_bridge.c source/verified_geometry_pair.c \
 source/verified_primitive_draw.c tests/c179_private_geometry_draw_probe.c -o "$tmp"
"$tmp" "$@"
