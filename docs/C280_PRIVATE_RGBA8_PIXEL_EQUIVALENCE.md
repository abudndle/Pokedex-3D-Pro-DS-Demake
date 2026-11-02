# C280 — Private 32-bpp original C5 to C78 P3PX exact-pixel differential

Private authorized source C56, C73 SHA anchors and the existing private C78 P3PX conversion were compared across **all 730 original models**. The 32-bpp source candidate layout uses **8×8 Morton tiles (x-bit first), vertically flipped output, source bytes A,R,G,B, RGB channels shifted right by 3, and alpha threshold >=128** to produce A1RGB555 P3PX v2. **All 412 same-dimension original 32-bpp textures match C78 P3PX byte-for-byte across 20,405,248 pixels.** Four 32-bpp textures were resized in C78 and are explicitly excluded from exact-pixel claims. Every tested original source range is C73 offset/size/SHA-anchored.

This is strong **source-to-prior-conversion consistency**, NOT independent original PICA200 pixel semantics, GPU sampler roles, 3DS reference screenshot fidelity, or an asset-integrated DS/DSi ROM rendering test. C78 is itself original-derived and not independent reference truth. Do not extrapolate to 4/8/16/24-bpp classes or the 33 unanchored C73-missing descriptors.

The public source contains only the generic bounded converter, private ZIP comparison gate, and synthetic Morton/channel/alpha/CRC/header tests. The actual Nintendo source C56/C73/C78 ZIPs, pixel bytes, private SHA reports, converted textures and ROMs remain private. Private report writes are atomic 0600; only aggregate counts print to stdout.

Private invocation:

```sh
python3 tools/c280_private_rgba8_pixel_equivalence.py \
  --private-root /private/c56 \
  --c73-csv /private/C73_TEXTURE_BYTE_PROVENANCE.csv \
  --p3px-zip /private/C78_PRIVATE_ORIGINAL_DS_A1_TEXTURES.zip \
  --output-private-json /private/reports/c280.json --require-full
```

Next C281: independently validate source 24-bpp RGB8 channel order and Morton tiling against C78 conversion, then 16/8/4-bpp source classes; only claim original GPU semantics after independent reference evidence. Issue #138 remains OPEN until original sampler-to-material/P3PX bindings and private asset-integrated emulator visuals are proven.
