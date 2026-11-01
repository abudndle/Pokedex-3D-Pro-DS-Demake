#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -DC7_TEST_HOST -Isource source/verified_primitive_stream.c source/verified_primitive_bridge.c source/verified_primitive_draw.c tests/c176_native_primitive_draw.c -o "$tmp"
"$tmp"
