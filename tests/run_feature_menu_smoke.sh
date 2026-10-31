#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/feature_menu.c source/dsi_features.c tests/test_feature_menu_smoke.c -o "$tmp/test"
"$tmp/test"
