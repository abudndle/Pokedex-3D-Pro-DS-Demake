#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
  source/records.c source/save_store.c tests/test_c81_records.c \
  -o "$tmp/test_records"
"$tmp/test_records" "$tmp/records"
