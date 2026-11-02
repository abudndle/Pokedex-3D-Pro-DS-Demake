# C184 — Verify original C56 coverage without rejecting authentic 0x26 markers

## Real private-source observation

A read-only offline audit of the three authorized original C56 decoded C5 ZIPs found:

- **730/730** unique expected source model IDs (0–733 excluding 721–724); **0 missing or duplicate IDs**.
- Complete ZIP member decompression and CRC checks; all three whole-archive SHA-256 digests match the owner's previously saved private C150 baseline.
- **723** models with strict zero-valued reserved descriptor fields and **7** with the original-source `0x26` marker in the fifth word of one or more primary descriptors.
- The seven marked models are IDs 076, 077, 145, 377, 391, 663, and 729. The existing original C56 decoder/validator `tools/validate_c56.py` already explicitly accepts this *exact* marker when the other reserved word is zero.
- No invalid descriptor bounds or unexpected reserved words under the C56 validator's rules.

C180's earlier summary wrongly rejected those seven source models by treating *all* nonzero fifth descriptor words as structural corruption. This milestone brings the C180 private audit into agreement with the original C56 validator. All other nonzero reserved values still fail, and the flagged models remain visible in the private report.

## Validation

`python3 -m unittest discover -s tests -p 'test_c180_private_c5_coverage.py' -v` covers an asset-free synthetic 730-model roster, exactly seven warning-model cases, unknown/misplaced reserved flag rejection, failure and filesystem safety regressions. CI runs the same suite in `port-source-tests.yml`.

For authorized local C56 originals, run:

```sh
python3 tools/c180_private_c5_coverage.py \
  /private/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
  /private/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
  /private/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --report /private/C184_C56_INVENTORY.json
```

The report includes original source hashes, so it **must stay private**. Do not upload the C56 archives, converted model data, hashes, or release ROM to this public repository or Actions artifacts.

## What is *not* complete

This establishes **original C5 file inventory and descriptor-bound checks**, not original vertex attributes, triangle topology, skinning, texture/sampler binding, 3DS shader parity or native Nintendo DS visual fidelity. The privately recovered C84 package has 4,039 original-derived P3PX textures but only 10 upper-screen UI bitmaps, and C98 contains 500 P3CS chunked models, not a finished full set of original-equivalent DS geometry. Original lower-screen UI, title assets, verified P3VX/P3IX transports and asset-integrated emulator/hardware testing still block final-release `make`.

Do not mark the complete port or original-art release gate finished on the strength of this milestone.
