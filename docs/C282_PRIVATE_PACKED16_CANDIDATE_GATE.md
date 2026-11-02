# C282 — bounded private 16-bpp original-source texture candidate gate

This source-only tool tests **ten explicit candidate 16-bit channel layouts** against previously converted C78 P3PX v2 A1RGB555 pixels. It preserves C279's source C5 texture boundaries and requires independent C73 SHA anchors. Each original 8×8 Morton-tiled source texture is compared at identical dimensions with the C78 texture; resized or unanchored textures are excluded, not counted as exact. A unique full-pixel match is **only evidence of consistency with C78**, not an independently decoded original PICA200 GPU format. Uniform textures may match multiple layouts; ambiguous matches and zero matches are separately reported, never silently assigned a format. Source material/sampler identities remain unverified.

Supported hypotheses: RGB565 and BGR565, ARGB1555 and ABGR1555, RGBA5551 and BGRA5551, RGBA4444 and ABGR4444, and both luminance/alpha byte orders. These are candidates, not assertions about Nintendo's original format. Unsupported source formats, compression and palettes must not be relabeled. The tool rejects malformed C5/C78 archive members, symlinks, duplicate models/textures, missing P3PX textures, invalid P3PX headers, incorrect source SHA anchors and over-budget input. Reports use the existing atomic private mode-0600 writer; the CLI prints only aggregate statistics.

Private-only invocation (paths are placeholders; do not upload these inputs or the output):

```sh
python3 tools/c282_private_packed16_candidates.py \
  --private-root /private/c56 \
  --c73-csv /private/C73_TEXTURE_BYTE_PROVENANCE.csv \
  --p3px-zip /private/C78_PRIVATE_ORIGINAL_DS_A1_TEXTURES.zip \
  --output-private-json /private/reports/c282.json --require-full
```

Public CI uses nine synthetic tests, including a synthetic ZIP audit and a source SHA mismatch rejection. The full 730-model private audit, actual source layout classification, 8/4-bpp decoding, GPU sampler assignment, original-asset ROM testing, and visual comparison are **not established by these tests**. Follow-on C283 should perform private batch classification and independently corroborate GPU format/channel semantics, then recover explicit source sampler/P3PX bindings; keep issue #138 open until actual original material mapping and emulator rendering are proven.
