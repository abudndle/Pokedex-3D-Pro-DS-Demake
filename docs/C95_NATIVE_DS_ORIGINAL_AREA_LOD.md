# C95 — Original-face area-stratified 600-triangle Nintendo DS preview LOD

This milestone is a **genuine source-geometry quality improvement** within the existing native 600-triangle preview budget. It selects larger original triangles from each source-order interval rather than replacing them with generated geometry. The original C90 per-mesh material indices and recovered original UV pairings remain attached to the same source faces.

## Verified private batch

| Metric | C95 private result |
|---|---:|
| Recovered complete-UV source models converted | 500 |
| Full original source triangles examined | 2,396,500 |
| Original-derived native DS preview triangles | 300,000 |
| Source material ranges preserved | 2,147 |
| Original-derived color-texture candidates | 1,152 |
| Average old source-surface area retention | 14.47% |
| Average C95 source-surface area retention | 20.14% |
| Models with a source-area improvement | 500 |
| Models with source-area regression | 0 |
| Exceeded 600-triangle native geometry budget | 0 |
| Original 3DS texture sampler assignments independently proven | **0** |
| Original 3DS visual fidelity certified | **0** |

The private converter processed the original C62/C7 UV-bearing OBJ source, independently checked the source against C94 SHA256, preserved each source mesh boundary, and produced matching DS3M/P3UV/P3MT candidate triples. The **provisional** C92 color-texture images were carried over unchanged, with existing P3TX manifests. ZIP member count: **3,153**, CRC and native geometry/UV/material/texture checks pass. The 500-model HTML viewer packs the exact same source-derived candidate assets.

The improvement metric is the sum of triangle areas represented by the chosen source faces, divided by total source triangle area. This is **not** perceptual similarity, source silhouette accuracy, source face coverage, material accuracy, skeletal animation, or final Nintendo DS fidelity. The 600-face previews still look sparse compared with full recovered geometry. The C94 full-OBJ browser remains a separate visual-reference asset.

## Source selection algorithm

For each original mesh, retain its original per-mesh triangle quota (up to 600 total for the model). Find the prior deterministic midpoint face index for each quota interval. Divide original face order into contiguous strata around those anchors. Select the maximum-area **existing original face** in each stratum, tie-breaking by lowest original face index. Because the prior midpoint is a candidate within its own interval, total selected triangle surface area cannot decrease; selected triangles preserve their source UV and C90 original material range. Do not claim this provides a watertight source mesh, exact polygon topology reconstruction, or source 3DS appearance.

## Public-safe repeatability

```sh
python3 tools/c95_original_source_lod_quality.py \
  --stage /private/C95_PRIVATE_AREA_STRATIFIED_DS_PREVIEW_NITROFS.zip \
  --report /private/C95_MODEL_SURFACE_RETENTION_REPORT.json \
  --require-full-c95
```

The public tool reuses the existing C92 asset-integrity auditor, checks the per-model area/mesh/material provenance, and **always labels output unapproved for release**. The public host tests use synthetic triangles and diagnostic files; no commercial game assets or extracted textures are committed to GitHub.

The private browser was opened headlessly in Chromium and successfully rendered p000 and p025 with no JavaScript errors. Those screenshots are not original-game comparison evidence.

## Next milestone

C96 should address visual sparsity and DS GPU performance with source-backed submesh LOD streaming, then visually compare native screenshots against the complete original C94 browser and lawful 3DS captures. Source sampler mapping, 38 original color-channel exceptions, 162 partial UVs and the remainder of the full game are still unresolved. The C85 final release gate remains blocked.
