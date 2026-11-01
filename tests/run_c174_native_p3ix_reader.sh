#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -Isource source/verified_primitive_stream.c tests/c174_native_p3ix_reader.c -o "$tmp"
"$tmp"
