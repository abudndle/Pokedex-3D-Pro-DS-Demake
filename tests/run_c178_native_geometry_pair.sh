#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
  source/verified_vertex_stream.c source/verified_primitive_stream.c \
  source/verified_primitive_bridge.c source/verified_geometry_pair.c \
  tests/c178_native_geometry_pair.c -o "$tmp/probe"
"$tmp/probe" "$tmp/vertices.p3vx" "$tmp/indices.p3ix"
