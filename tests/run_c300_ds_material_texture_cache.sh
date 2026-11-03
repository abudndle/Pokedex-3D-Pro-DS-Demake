#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -DC7_TEST_HOST -Isource \
  source/model_textures.c source/texture_pixels.c source/texture_asset.c \
  source/ds_texture_upload.c source/ds_material_texture_cache.c \
  tests/test_c300_ds_material_texture_cache.c -o "$tmp/test-c300"
(cd "$tmp" && ./test-c300)
