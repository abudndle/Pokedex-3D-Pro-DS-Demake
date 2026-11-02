# C284 — source-SHA-backed ETC1/ETC1A4 vertical orientation candidates

C284 extends the bounded C283 private C56 original-C5/C84 P3TM SHA-backed texture differential with **two explicit** ETC1/ETC1A4 vertical-orientation hypotheses: original C283 vertically flipped and an otherwise identical unflipped 3DS-style little-endian 4×4-block/8×8-tile arrangement. It reports all exact matches, including ambiguity when both orientations match. It never infers GPU format from 4/8-bpp density. Existing C283 behavior remains unchanged without the optional callback.

## Private full 730-model evidence — November 2, 2026

All 730 C56 models and C84 P3TM catalogs were checked privately. Of 317 low-bpp source descriptors, four lacked P3TM SHA anchors and one had resized P3PX output and were excluded. Across the remaining 312 SHA-anchored, same-dimension descriptors, **190** had a unique candidate consistent with prior C84 conversion (148 L8, 39 ETC1 unflipped, 3 ETC1A4 unflipped), covering **4,106,496 A1RGB555 pixels**. One descriptor matched both ETC1 orientations and remains **ambiguous**. **121** had no supported candidate: opaque source format 0x0000675a (98), 0x0000675b (21), 0x67616757 (2). Compared with C283's 149 unique candidates, the extra orientation yields 41 net additional unique candidates while converting the one former flipped match to ambiguous. The evidence is **only conversion consistency**, not independently decoded original PICA200 format or material/sampler binding.

No private source pixels, hashes, texture ZIPs, reports, ROMs or proprietary conversions were committed. Public CI uses eight synthetic C284 regressions plus the twelve existing C283 regressions; native BlocksDS ROM/header and asset-free DeSmuME remain separate CI gates. Real asset-integrated rendering, animation, original shader/texture-unit semantics and 3DS visual parity remain unverified. Issue #138 remains OPEN.

Private-only run:

```sh
python3 tools/c284_private_etc1_orientation.py \
  --private-root /private/C56 \
  --c84-zip /private/C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip \
  --output-private-json /private/reports/c284.json --require-full
```

**Next C285:** Independently resolve the remaining 121 unmatched compressed/paletted candidates using source GPU format/sampler commands, alternate block/alpha ordering and reference render evidence. Avoid treating C84 as an independent 3DS GPU oracle. Only bind textures to meshes after source-verified sampler/material identity and private native rendering acceptance.
