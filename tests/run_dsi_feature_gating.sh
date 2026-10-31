#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource source/dsi_features.c tests/test_dsi_feature_gating.c -o "$tmp/test"
"$tmp/test"
