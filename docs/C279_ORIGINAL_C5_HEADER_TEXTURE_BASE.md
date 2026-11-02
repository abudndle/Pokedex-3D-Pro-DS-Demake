# C279 — Original C5 header-relative texture payload base (private)

Private source evidence independently recovers the original texture payload base as **little-endian C5 u32 at file offset +0x04, plus 0x78**. This is **not** C277's EOF-derived candidate. Across all three authorized C56 ZIP parts, the formula yields **4,072 bounded, contiguous original source texture ranges for all 730 models**. Every one of the **4,039 existing C73 offset/size/SHA records** matches the header-derived original C5 bytes, across 726 C73-covered models. C5 texture descriptors contain **height u16 at +16, width u16 at +18, opaque format u32 at +20**; all 4,039 C76 P3TM records independently match those source descriptor fields. The remaining **33 ranges in four C73-absent models** have bounded header-derived source offsets, byte lengths, format words and dimensions, but are **not independently SHA-anchored against C73**.

Private 730-model results: 4-bpp storage = 140, 8-bpp = 177, 16-bpp = 1,527, 24-bpp = 1,812, 32-bpp = 416; 12 distinct source format-word/size classes were previously observed. These are byte-density and opaque format fields, **not proven 3DS GPU format semantics**. The 33 C73-absent candidates comprise four 8-bpp, eighteen 16-bpp and eleven 24-bpp source descriptors.

The tool preserves source SHA and ranges only in a private atomic 0600 report, emitting aggregate counts to stdout. Public source and synthetic tests contain no Nintendo-derived data. It rejects malformed headers, noncontiguous descriptor offsets, invalid dimensions, out-of-bounds payloads, mismatching C73 anchors or C76 format metadata, duplicate/invalid ZIP IDs, symlinks and over-budget archives. No private ZIP, texture, SHA manifest, report or ROM is published.

Private invocation:

```sh
python3 tools/c279_private_header_texture_base.py \
  --private-root /private/c56 \
  --c73-csv /private/C73_TEXTURE_BYTE_PROVENANCE.csv \
  --catalog-zip /private/C76_ALL_730_TEXTURE_CATALOGS_PRIVATE.zip \
  --output-private-json /private/reports/c279.json --require-full
```

**Limits:** Header-based source byte extraction does not prove 3DS texture channel order, swizzling, compression, alpha, GPU sampler assignment, P3PX pixel fidelity, full original-model rendering or DS/DSi visual parity. Next C280: format-specific pixel decode with independent reference checks, especially four-bit storage, followed by private asset-integrated emulator/hardware QA. Keep issue #138 OPEN.
