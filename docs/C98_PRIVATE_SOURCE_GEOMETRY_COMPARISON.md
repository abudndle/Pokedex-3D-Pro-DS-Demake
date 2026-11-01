# C98 — Reversible native DS source-geometry comparison

C98 addresses a real integration problem: when both legacy DS3M and newer chunked P3CS exist, the native preview loader always used DS3M. A combined private NitroFS therefore could silently hide the new geometry.

## Native change

- The default remains **LEGACY**, preferring the original-derived 600-triangle DS3M.
- Settings **X** toggles **HIGH (TEST)**; the loader tries the valid P3CS model first and streams up to 1,800 source-sampled triangles using the existing 600-triangle buffers.
- Missing or corrupt P3CS falls back to the legacy DS3M. If neither file validates, the preview is unavailable; source geometry is not invented.
- Settings X switches back to the legacy preview. This preference is runtime-only and is not written to user saves.
- The model rotation, original UI artwork, and existing Dex navigation remain unchanged. SELECT shows text-mode navigation where the private original art covers instructions.
- Chunked previews remain geometry-only: original 3DS GPU sampler semantics have NOT been independently verified.

## Private combined source-asset test package

The user's private C98 comparison NitroFS ZIP has **6,738** entries: 726 original-derived C86 legacy previews and 500 original-derived C96/C97 P3CS chunked previews (1,499 chunks; 893,666 selected source triangles). It also stages recovered original UI artwork, English Dex data, original move names and original-derived texture metadata/images. The package is private and does not belong in public GitHub.

The test-only P3SM species resource map contains exactly three diagnostic entries: Dex entries 1, 2, and 25 route to source resources p000, p001 and p025. These deliberately narrow test associations are **not an authentic recovered source-game species map** and must never ship as original gameplay data.

All 500 P3CS original-source headers, CRC32 indices, chunk payload checksums, triangle counts, and file lengths passed independent local validation. Each chunked model has a corresponding legacy model. The full ZIP CRC passed. No 3DS visual-fidelity or private emulator performance result is claimed.

## Reproduce privately

With the user's private original-derived C86 and C96 ZIPs:

```sh
python3 tools/c98_build_private_geometry_qa_nitrofs.py --legacy-zip /private/C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip --chunk-zip /private/C96_PRIVATE_CHUNKED_1800_TRIANGLE_NITROFS_v2.zip --out /private/C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip
```

Extract the NitroFS ZIP directly into a local, private project's nitrofs folder and build a **development-only** ROM with BlocksDS:

```sh
make -f Makefile.native NITROFSDIR=nitrofs rom
```

Never bypass the C85 final-release gate. Keep the Nintendo-derived original model and texture data out of this repository.

## Regression verification

The existing host preview regression now tests both assets at one model ID: legacy selected by default; high-detail selected after an explicit toggle; invalid P3CS falling back to intact DS3M; corrupted P3CS without a fallback rejected; switching back restoring legacy. The new public-safe ZIP packager includes CRC, roster, and diagnostic-map synthetic tests.

**Still unfinished:** private asset-bearing ROM screenshot and hardware/emulator frame-time evidence, independently verified original GPU material/texture sampler channels, full source mesh geometry on DS, authoritative source species mapping, animation and gameplay parity. This is a native QA feature, not a complete 3DS port.
