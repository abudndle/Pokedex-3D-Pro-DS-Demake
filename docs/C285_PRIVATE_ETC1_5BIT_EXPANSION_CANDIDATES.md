# C285 — original C5 ETC1 5-bit expansion candidates (private-only)

C285 tests a second ETC1/ETC1A4 **differential-mode 5-bit base expansion** against the C84 prior original-derived P3PX conversion: integer-floor `v*255//31` versus the existing bit-replication `(v<<3)|(v>>2)`. Both are tested in flipped/unflipped vertical orientations. A single-channel difference can distinguish the candidates (5-bit base 20, modifier −5: integer-floor gives A1RGB555 red 19, bit replication gives red 20). All hypotheses remain visible; when multiple agree, the descriptor is **ambiguous**. C283/C284 default behavior remains unchanged.

## Private 730-model differential — November 2, 2026

All 730 original C56 models and 730 C84 P3TM source-SHA catalogs were checked privately. Of **317** low-bpp descriptors, **4** had no P3TM source-SHA anchor and **1** had resized C84 output, so were excluded. For the remaining **312** source-SHA-anchored same-size descriptors, **all 312 have at least one pixel-exact candidate consistent with C84**. **269** have exactly one tested candidate (148 L8, 100 ETC1 unflipped floor5, 21 ETC1A4 unflipped floor5) across **4,263,424 A1RGB555 pixels**; **43** have multiple equally matching candidate decoders and remain explicitly ambiguous (another 143,872 pixels). **Zero** of the 312 are unmatched under these bounded hypotheses. This is a reproducible C56/C84 **conversion-consistency result**, **not** independent evidence of original PICA200 GPU format IDs, alpha/sampler/material binding, correct source shaders, hardware output or 3DS visual fidelity. The 43 ambiguous must not be marked uniquely decoded.

No Nintendo source bytes, private SHA manifests, converted images, ROMs, private reports or model payloads are included in public GitHub or CI. Synthetic C285 tests cover differential expansion, ETC1/ETC1A4 alpha, vertical orientations, malformed inputs and ambiguity. Native BlocksDS/ROM/header and asset-free DeSmuME remain separate gates.

Private-only command:

```sh
python3 tools/c285_private_etc1_quantization.py \
  --private-root /private/C56 \
  --c84-zip /private/C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip \
  --output-private-json /private/reports/c285.json --require-full
```

**Next C286:** Obtain independent original texture-unit format/alpha/tile commands and mesh-to-material/sampler identity, resolve the 43 ambiguous decoder variants, and prove original textures rendered on native DS/DSi using authorized private assets and real emulator/hardware captures. Keep issue #138 OPEN until this evidence exists; do not confuse C84 self-consistency with original GPU verification.
