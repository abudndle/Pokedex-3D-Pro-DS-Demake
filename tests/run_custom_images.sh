#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/custom_images.c tests/test_custom_images.c -o "$tmp/custom_images_test"
"$tmp/custom_images_test"
