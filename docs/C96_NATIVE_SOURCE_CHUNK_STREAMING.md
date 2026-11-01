# C96 — CRC-checked original-source geometry streaming on native Nintendo DS

C96 removes the **single 600-triangle total** limitation for *geometry-only
diagnostic* previews by keeping only one 600-triangle chunk in the existing
vertex, UV and face-color buffers. Source model geometry is still sampled and
simplified; it is not the full original Nintendo 3DS polygon budget.

## Private batch (original-derived source only)

- **500/500** recovered UV-equipped diagnostic models converted without source
  model, source UV, original C90 material index, or face-order mismatches.
- **893,666** original-derived sample triangles in **1,499** individual P3CS
  chunks, maximum **600 per chunk** and **1,800 per model** (p710 has 1,184).
- The first pass found source model **p277** contains intervals of source
  zero-area triangles. C96 now preserves the selected *original* zero-area face
  instead of inventing geometry or refusing the whole model.
- Source area retained, mean across 500 models: **42.54%** original midpoint
  sample vs **48.78%** revised source-area-stratified choice, at the same
  1,800-triangle sampling budget. No model's *measured surface area* regressed.
- The private package contains 500 `preview/pNNN.p3cs` files, 500 experimental
  `materials/pNNN.p3mt` files, 500 P3TX manifests, 1,152 reduced-size
  original-derived P3PX images, and an explicit experimental warning README.
- All original-derived color sampler selections are **C92 name-based
  experimental hints**. They are NOT independently proven Nintendo 3DS GPU
  texture channel bindings; neither normal maps nor effects may be silently
  substituted for color maps. This remains a private visual diagnostic.

## Native P3CS format and bounded reader

A P3CS file has a 24-byte little-endian header:
`P3CS`, version u16=1, model ID u16, chunk count u16 (1–3),
reserved u16=0, selected triangles u32 (1–1800), original triangles u32,
chunk-index CRC32 u32.

Each of the 1–3 index entries has 16 bytes: first triangle u32,
chunk triangle count u16 (1–600), reserved u16=0, byte offset u32 and
payload CRC32 u32. Consecutive entries have no gaps. Each selected triangle
uses 33 bytes: nine signed 4.12 XYZ int16s, six signed 4.12 UV int16s and
three neutral RGB888 face-color bytes. Source vertex order is preserved.

`p3dChunkOpen` verifies all table offsets, row counts, CRCs, payload size,
model ID and complete coverage **before** declaring the stream ready. It
checksums each source chunk in bounded 128-byte reads. `p3dChunkRead`
reads only a single chunk into caller-owned buffers and checks its CRC again.

The existing `previewStreamLoad` keeps legacy `pNNN.ds3m` behavior
unchanged. **Only when no DS3M exists**, it tries `pNNN.p3cs`. In chunk
mode the renderer loops over chunks and draws source triangles in the existing
600-triangle static buffers, rather than allocating a 1,800-triangle model in
RAM. Chunk UVs are loaded for positional integrity but **textured rendering
remains disabled**, because the existing P3MT texture-map reader only accepts
up to 600 triangles and sampler roles remain unverified. External range-draw
calls are rejected for chunk mode; the path is explicitly geometry-only.

## Public-safe checks

- Local native C host reader validates original-derived p000's three chunks
  and rejects wrong model ID and corrupted payload CRC.
- Private ZIP passed member integrity and inventory checks for all **2,653**
  members (500 P3CS + 500 P3MT + 500 P3TX + 1,152 P3PX + 1 README).
- Public CI uses only a generated **synthetic** 1,202-triangle P3CS and a
  corrupted variant. It tests native readback, legacy DS3M compatibility,
  bounded streaming of all triangles and fail-closed behavior.
- `make dev-rom` still builds an **asset-free** smoke ROM. Full original
  gameplay, animation, materials, accurate visuals and C85 release gating
  remain unfinished.

## Private test procedure

Extract **only** the `diagnostic_nitrofs/` contents to a separate local
test NitroFS root with the required legally obtained support assets; do not
copy this package into the final release tree or public GitHub. The native
preview uses a P3CS only when no `.ds3m` exists for that same model ID.

The full private generator is `c96_build_chunked_ds_lod.py`, built on
the user's C86/C90/C92/C94/C95 original-derived source archives and
checksums. The private full-batch report is
`C96_500_MODEL_STREAMING_REPORT.json`.

Next technical priorities: validate the native chunked view in an emulator
with the **private** dataset; independently decode original sampler units
and texture combiners; profile DS hardware frame rate and optimize source
geometry scheduling without losing source mesh/material associations.
