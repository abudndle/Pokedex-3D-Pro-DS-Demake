#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/save_store.c tests/test_save_store_smoke.c -o "$tmp/test"
"$tmp/test" "$tmp/save"
