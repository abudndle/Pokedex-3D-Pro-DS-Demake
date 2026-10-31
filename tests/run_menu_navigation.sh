#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)";trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/menu_layout.c source/menu_navigation.c tests/test_menu_navigation.c -o "$tmp/test"
"$tmp/test"
