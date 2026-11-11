#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -Isource \
 source/nitro_source_bridge.c tests/c335_nitro_source_bridge.c -o "$tmp/c335"
"$tmp/c335"
cc -std=c11 -Wall -Wextra -Werror -O2 -DP3D_USE_NITRO_ENGINE \
 -Dfopen=test_fopen -Itests/nitro_engine_stub -Isource \
 -c source/nitro_source_bridge.c -o "$tmp/adapter.o"
cc -std=c11 -Wall -Wextra -Werror -O2 -DP3D_USE_NITRO_ENGINE \
 -Itests/nitro_engine_stub -Isource tests/c335_nitro_source_bridge.c \
 "$tmp/adapter.o" -o "$tmp/c335-adapter"
"$tmp/c335-adapter"
