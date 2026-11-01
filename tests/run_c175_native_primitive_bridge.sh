#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -Isource source/verified_primitive_stream.c source/verified_primitive_bridge.c tests/c175_native_primitive_bridge.c -o "$tmp"
"$tmp"
