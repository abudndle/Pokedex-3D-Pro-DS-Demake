#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
  source/verified_vertex_stream.c source/verified_primitive_stream.c \
  source/verified_primitive_bridge.c tests/c177_native_vertex_stream.c -o "$tmp"
"$tmp"
