# C283 — private original low-bpp/ETC1 texture candidate gate

C283 adds a source-only, SHA-backed C56 original-C5 → C84 original-derived P3PX differential for 8- and 4-bpp **storage-density** classes. It tests Morton-tiled L8/A8/LA44 and L4/A4 nibble hypotheses, plus 3DS-style ETC1/ETC1A4 little-endian 4×4 blocks in 8×8 tiles. Original C5 header-relative byte extents are checked against C84 P3TM source offsets, SHA-256, dimensions and opaque format words. The C84 P3TM data is **prior original-derived conversion metadata**, not independent GPU evidence.

## Private 730-model evidence — November 2, 2026

All 730 original C56 models and 730 C84 P3TM catalogs were inspected privately. Of **317** low-bpp descriptors (140 at 4 bpp, 177 at 8 bpp), four lacked a P3TM SHA anchor and one had a resized P3PX and were excluded. Of the remaining **312** same-dimension SHA-anchored descriptors, **149** matched exactly one candidate (148 L8 and one ETC1 little-endian tiled), across **3,963,648** A1RGB555 pixels. **163 did not match any supported candidate**: source format words 0x0000675a (137), 0x0000675b (24), 0x67616757 (2). No ETC1A4 match was established. These are conversion-consistency results, **not** independently proven original PICA200 format/sampler semantics. The one ETC1 candidate does not justify labeling the other 137 descriptors ETC1.

The audit rejects unexpected/duplicate ZIP texture or catalog members, symlinks, over-budget source or output, source SHA mismatches, bad P3PX headers and resized textures. It writes a private mode-0600 report and prints aggregate counts only. No original Nintendo data, source hashes, converted textures, reports, private ROMs or screenshots enter GitHub or CI.

### Private-only invocation

```sh
python3 tools/c283_private_low_bpp_candidates.py \
  --private-root /private/C56 \
  --c84-zip /private/C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip \
  --output-private-json /private/reports/c283.json --require-full
```

## Next C284

Investigate the 163 unmatched compressed/paletted candidates without changing the 149 already consistent conversions. Cross-check alternative ETC1 block ordering/alpha swizzle against independent GPU format commands or original rendering evidence; only verified original mesh/material/sampler-to-P3PX assignments may be used for native drawing. Issue #138 remains OPEN. This test does **not** verify private asset-integrated DS emulator rendering, original material shading, or visual parity.

Public technical background: https://www.3dbrew.org/wiki/CGFX and https://github.com/ObsidianX/3dstools/blob/master/bcfnt.py .
