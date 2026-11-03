#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
 source/nitro_source_bridge.c tests/c335_nitro_source_bridge.c -o "$tmp/c335"
"$tmp/c335"
