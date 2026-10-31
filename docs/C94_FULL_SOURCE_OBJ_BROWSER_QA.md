# C94 — Full recovered OBJ geometry for every C92 browser candidate

C94 expands the user's PRIVATE C93 browser visual-review milestone, replacing **all 500** 600-face sampled diagnostic models with their **full available source-recovered C7 OBJ triangles**. It is not a new native DS renderer or final 3DS-quality textured model release.

## Verified private checkpoint

- **500/500** browser candidates have recovered source UV-bearing OBJ data.
- **491** get UV-bearing geometry from the C62 recovered UV export; **nine** use earlier C7 UV-bearing exports.
- Every UV-bearing source OBJ's exact original C7 vertex text, ordered triangle vertex indices and mesh group order were cross-checked. **Zero** geometry/face-order mismatches.
- **2,396,500** source-derived full OBJ triangles embedded in the new private 500-model viewer, compared to 331,875 in C93. **Zero sampled-geometry fallback models** remain in C94 browser assets.
- **1,152** original-derived diagnostic color images remain embedded, with the C92 name-based source sampler choices clearly flagged provisional.
- All 500 compressed/decompressed model blobs, DS3M/P3UV/P3MT pairings and individual P3PX pixels passed SHA256/format readback validation. Zero embedded hash errors.
- Headless Chromium rendered and switched among p000, p002, p025, and p382 (the last has **12,526 recovered triangles**), with diverse nonblank canvas images and no JavaScript errors.
- **Six** private local source-geometry regression tests and **seven** public synthetic source tests cover face order, changed vertex coordinates, bad UV references and oversized UVs. Public CI never needs the original source archives.

The new 42.8 MB standalone HTML is **private** and local-only; it does not upload game assets or rely on external JS. The builder and user-private provenance records are packaged separately.

## Critical scope limits

The C62 UV exports were recovered using source data and may contain **inferred UV placement**; preserved OBJ topology does not prove accurate original 3DS UV values. The C92 texture sampler associations are **name/shader-based experimental choices**, not an independently decoded original 3DS GPU combiner. The browser rasterizer does not reproduce all original lighting, skeletal animation, normal/specular effects, transparency, or the full Pokédex interface.

Most important: these 1,184–12,526-triangle source meshes are **browser-only** diagnostics. The native DS preview renderer still uses at most **600 sampled triangles per model**, and C94 does **not** claim all 500 can run at full source-poly density on DS hardware.

The remaining 230 original source resource slots, 38 ambiguous color/material cases, 162 partial-UV meshes, four missing model/texture previews, unported challenges, sound and DSi features are still outstanding. The C85 release gate must remain blocked.

## Re-run the public-safe original OBJ alignment audit

```sh
python3 tools/c94_original_obj_uv_alignment.py \
  --original-c7 /private/Pokedex3D_C7_Validated_Geometry_OBJ_Collection.zip \
  --recovered-c62 /private/Pokedex3D_C62_528_UV_Model_Exports.zip \
  --model-ids /private/C94_PRIVATE_MODEL_IDS.json \
  --out /private/C94_OBJ_ALIGNMENT.json
```

All originals and browser output stay outside public GitHub. Next: compare original 3DS screenshots to the private browser result to identify inaccurate normals, UVs, color combinations, shading and alpha; then restore the remaining model resources and DS-specific streaming/LOD as independently verified.
