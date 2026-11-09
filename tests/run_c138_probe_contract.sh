#!/bin/sh
# Public, asset-free contract test for the private native model probe.
set -eu
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST \
  -Itools/host_stub -Isource \
  source/preview_stream.c source/preview_chunk_stream.c source/model_uv.c \
  tests/c138_native_preview_probe.c -o "$tmp/c138_probe"
for invalid in -1 731 abc 49junk ""; do
  if "$tmp/c138_probe" "$invalid" >"$tmp/out" 2>&1; then
    echo "C138 accepted invalid UV count: $invalid" >&2
    exit 1
  fi
  if ! grep -q 'expected UV count must be an integer' "$tmp/out"; then
    echo "C138 invalid UV count did not fail at argument validation" >&2
    cat "$tmp/out" >&2
    exit 1
  fi
done
echo 'C138 private native probe: public compilation and argument contract PASS'
