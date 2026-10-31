#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/search_touch.c \
    tests/test_c83_search_touch.c -o "$tmp/test"
"$tmp/test"
