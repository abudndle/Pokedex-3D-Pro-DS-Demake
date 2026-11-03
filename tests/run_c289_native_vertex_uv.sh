#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
  source/verified_vertex_stream.c source/verified_primitive_stream.c \
  source/verified_primitive_bridge.c source/verified_geometry_pair.c \
  source/verified_vertex_uv.c source/verified_primitive_uv_bridge.c tests/c289_native_vertex_uv.c -o "$tmp/probe"
"$tmp/probe" "$tmp/a.p3vx" "$tmp/a.p3ix" "$tmp/a.p3vu"
