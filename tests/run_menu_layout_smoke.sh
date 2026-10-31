#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/menu_layout.c tests/test_menu_layout_smoke.c -o "$tmp/menu_test"
"$tmp/menu_test"
