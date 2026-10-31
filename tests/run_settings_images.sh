#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/settings_images.c source/menu_layout.c source/custom_images.c tests/test_settings_images.c -o "$tmp/test"
"$tmp/test"
