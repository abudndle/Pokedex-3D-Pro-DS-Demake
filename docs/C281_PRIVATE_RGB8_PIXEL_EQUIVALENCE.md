# C281 — Private 24-bpp source RGB8 to C78 P3PX exact-pixel differential

Private owner-authorized C56/C73/C78 full 730-model comparison found that **all 1,771 same-dimension 24-bpp original-source textures** match the previously converted C78 A1RGB555 P3PX **byte-for-byte across 83,162,112 pixels**. Candidate source layout: 8×8 Morton tiles (x-bit first), vertical flip, source bytes R,G,B, each shifted right by 3, output alpha always 1. All compared source bytes have independently SHA-anchored C73 offsets. **30 resized 24-bpp textures and 11 C73-unanchored source descriptors are excluded**, not claimed pixel verified.

C281 extends C280's bounded private ZIP/source audit with a generic density/comparator callback, preserving C280's original 32-bpp behavior and tests. A fast optional NumPy path accelerates private 83M-pixel checks; the pure-stdlib converter remains tested in public synthetic CI. Private reports are atomic mode 0600 and only aggregate counts print. Nintendo source archives, original pixel bytes, SHA manifests, converted copyrighted assets and ROMs stay outside public GitHub and CI.

**This is consistency with C78's prior original-derived conversion, NOT independent original 3DS GPU pixel semantics or material sampler binding.** It does not verify 16/8/4-bpp source formats, the 33 unanchored C73 gaps, authentic asset-integrated DS rendering, or 3DS visual parity.

Private invocation:

```sh
python3 tools/c281_private_rgb8_pixel_equivalence.py \
  --private-root /private/c56 \
  --c73-csv /private/C73_TEXTURE_BYTE_PROVENANCE.csv \
  --p3px-zip /private/C78_PRIVATE_ORIGINAL_DS_A1_TEXTURES.zip \
  --output-private-json /private/reports/c281.json --require-full
```

Next C282: independently verify 16-bpp packed channel layouts and 8/4-bpp source classes against private C78 conversions and an independent PICA200 reference where possible, then source-proven original sampler/P3PX binding and private ROM/emulator visual QA. Issue #138 stays OPEN.
