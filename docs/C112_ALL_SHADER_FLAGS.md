# C112 — Preserve every original C5 shader declaration before texture routing

The user requires a **full original Pokédex 3D Pro Nintendo 3DS-to-DS port**, with the **original title screen unchanged** and original designs for all other screens. No replacement visuals or guessed shader assignments may be described as source-authentic.

## Source-faithfulness bug fixed

C110's private P3SC v1 converter only carried two of the original shader's declared `CF_*` capabilities: `CF_COLORMAP` and `CF_BUMPMAP`. Other real original capabilities, including `CF_CASTSHADOW` in the existing synthetic source fixtures, were discarded. That made a complex source shader look like a color-only shader in the DS renderer.

C112 upgrades private `P3SC` to **v2**, preserving the known `CF_COLORMAP` (bit 0), known `CF_BUMPMAP` (bit 1) and the presence of **any other** original `CF_*` capability (bit 2, `P3D_SHADER_CAP_OTHER`). The private extractor counts the number of materials requiring additional shader investigation, including color-mapped materials that declare bump or other shader operations. It never invents normal, specular, or effect sampler roles.

- **Private extraction:** regenerate `materials/pNNN.p3sc` from the user's own decoded C5 and cross-checked C75 original sources with `tools/c110_original_shader_capabilities.py`. Previous P3SC v1 output must be regenerated, **not relabeled**, because discarded source flags cannot be reconstructed from v1.
- **Native renderer:** refuses to upload a simple color texture when the source shader has `CF_BUMPMAP` **or any additional original C5 capability**. P3MT and P3TX must still match the original model and the C109 source material IDs.
- **Final private release audit:** now requires P3SC **v2** with valid CRC and only the three supported declaration/presence bits. Old v1 entries fail closed.
- **Tests:** synthetic C5 shader declarations containing extra `CF_CASTSHADOW`, known bump/colormap flags, invalid bits, a valid-CRC legacy v1 file, and an otherwise valid-CRC v2 record with extra original flags. The native host fixture rejects ambiguous texture routing; CI tests private asset staging and a native development ROM.

## What is not claimed

The exact original GPU sampler equations, normal/specular/effect routing, the correct appearance of every Pokémon model, and original shader behavior **remain unverified**. Preserving the presence of an unknown capability is safer than discarding it, but it does not decode that capability. The user's original decrypted source archives remain private and are not added to GitHub.

Further work requires source C5 shader-instruction decoding, per-material UV transforms, private original-asset comparison in melonDS or hardware, and complete UI/gameplay/audio/animation parity. The original 3DS title screen is not modified by C112.
