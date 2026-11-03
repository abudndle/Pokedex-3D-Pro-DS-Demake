#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -DC7_TEST_HOST -Isource \
  source/model_textures.c source/model_material_texture.c \
  source/texture_pixels.c source/texture_asset.c \
  source/ds_texture_upload.c source/ds_material_texture_cache.c \
  source/ds_material_uv_draw.c \
  tests/test_c304_native_material_transaction.c -o "$tmp/c304"
(cd "$tmp" && ./c304)
