#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST -Isource source/ds_texture_upload.c tests/test_ds_texture_upload.c -o "$tmp/test"
"$tmp/test"
