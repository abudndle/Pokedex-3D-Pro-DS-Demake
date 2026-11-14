#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
root="${1:?synthetic NitroFS root required}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -Wall -Wextra -Werror -O2 -DC7_TEST_HOST -Isource \
  source/verified_vertex_stream.c source/verified_primitive_stream.c \
  source/verified_primitive_bridge.c \
  source/verified_geometry_pair.c source/verified_vertex_uv.c \
  source/verified_primitive_uv_bridge.c source/verified_material_uv_draw.c \
  source/verified_material_uv_planned.c \
  source/model_materials.c source/model_textures.c source/model_material_texture.c \
  source/source_material_map.c source/source_shader_caps.c \
  source/source_material_words.c source/source_material_texture_match.c \
  source/source_color_ranges.c source/texture_pixels.c source/texture_asset.c \
  source/ds_texture_upload.c source/ds_material_texture_cache.c \
  source/ds_material_uv_draw.c tests/c306_native_texture_sidecar_probe.c \
  -o "$tmp/c306-probe"
"$tmp/c306-probe" "$root"
