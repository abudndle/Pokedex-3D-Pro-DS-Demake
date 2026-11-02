# C278 — Private original C5 texture byte-density evidence

C278 cross-checks the **source C5** texture table and contiguous tail candidates (C277), the independently saved **C73** source-offset/SHA prefix, and **C76 P3TM** catalog record identity, names, dimensions, opaque source format fields and CRC. It treats C277 EOF-tail positions as **hypotheses** and trusts only C73 offsets independently rehashed against actual source bytes. It rejects malformed P3TM records, mismatched anchored hashes, unsafe ZIP members, duplicate model IDs, out-of-budget input and inconsistent source catalog coverage. Because C76/C73 cover only 4,039 of 4,072 C5 descriptors, any C5 tail rows without P3TM metadata remain explicit NO_P3TM_METADATA records, never silently dropped or promoted. The tool reports aggregate storage-density classes (4/8/16/24/32 bits per pixel only when byte counts exactly fit), while retaining per-texture evidence in an atomic private 0600 JSON report.

## Private full-roster validation (2026-11-02)

The owner-authorized original C56 three-part ZIP, C76 P3TM catalog ZIP and C73 source provenance CSV were run privately with `--require-full`: **730/730 models**, **4,072 original C5 descriptors**, **4,039 C73/P3TM SHA-anchored source ranges**, and **33 C5 descriptors lacking P3TM metadata**. All 4,039 C73 source offsets/hashes match the C76 catalog and actual C5 source bytes, but **zero** of those anchored offsets/hashes match C277's EOF-derived contiguous-tail hypothesis. Therefore that EOF-base hypothesis is **refuted** for these anchored rows; it must not be used to recover the 33 missing textures. The bounded private audit completed successfully without publishing source bytes, names, offsets, hashes or converted assets.

Storage-density counts from the private audit: 4 bpp = 140; 8 bpp = 173; 16 bpp = 1,509; 24 bpp = 1,801; 32 bpp = 416; missing P3TM metadata = 33. These are only byte-length/dimension ratios, **not proven hardware formats**.

**A byte-density match is NOT a texture decoder.** The opaque format code has not been mapped to GPU pixel encoding, tiled/swizzled memory layout, channel order, compression or alpha behavior. P3TM metadata may derive from the same C5 extraction and cannot independently prove an unanchored C277 tail; the private C73 cross-check in fact disproves the EOF-tail offsets for all 4,039 anchored entries. Original GPU sampler roles, P3PX source-pixel equivalence, private asset-integrated ROM rendering and 3DS visual parity remain unverified. No source hashes, private texture names, offsets, model bytes, converted pixels or proprietary ZIPs belong in GitHub/CI.

Private-only usage:

```sh
python3 tools/c278_private_texture_format_evidence.py \
  --private-root /private/c56 \
  --catalog-zip /private/C76_ALL_730_TEXTURE_CATALOGS_PRIVATE.zip \
  --c73-csv /private/c73.csv \
  --output-private-json /private/reports/c278.json --require-full
```

Next: independently prove the opaque format-code to pixel-layout mapping with authorized original source and reference decoder evidence, including swizzle and compression; verify decoded source pixels against private P3PX output; then test real texture sampling on a private native DS/DSi ROM with emulator/hardware captures. Keep issue #138 open until sampler binding is proven.
