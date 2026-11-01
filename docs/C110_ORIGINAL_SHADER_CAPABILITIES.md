# C110 — Original 3DS C5 shader capability gate (sampler roles still unresolved)

## Scope

The goal is a faithful port of **all** Pokédex 3D Pro screens and gameplay with original private 3DS data. C109 verified that a candidate model texture was referenced by the original C5 material, but a material can reference multiple texture slots. A texture reference alone does not identify the diffuse/color sampler slot.

C110 adds a conservative native shader-declaration check. It **does not claim to have reverse engineered the original GPU shader execution or assigned every source color map**.

## Private original-C5 extraction

`tools/c110_original_shader_capabilities.py` reads the three private decoded C5 archives and the C75 original texture-name inventory. It reuses C88's original C5 shader/material pointer verification, rejects missing or mismatched source texture names, extracts original shader declarations, and emits CRC-protected model-specific `materials/pNNN.p3sc` records **only inside a private ZIP**. These contain original material index, shader index, both original referenced texture IDs, and C5 shader **declaration bits** for `CF_COLORMAP` and `CF_BUMPMAP`. They contain no texture pixels, shaders or meshes.

Example on a local computer with the user's own private game files:

`python3 tools/c110_original_shader_capabilities.py --private-root PRIVATE_C5_FOLDER --texture-reference-csv PRIVATE_C75_NAMES.csv --output PRIVATE_C110_SHADER_CAPS.zip --require-full`

The tool prints aggregate counts including ambiguous two-texture materials and **zero roles declared verified**. The private ZIP needs to be staged into the original-content NitroFS build. Do **not** upload Nintendo files or their extracted archives into public GitHub.

## Native render gate

The Pokémon texture loader first validates the preview geometry and P3MT/P3TX ranges (C108), then the CRC-protected source C5 P3MR mesh/material/texture references (C109), and now also requires a valid source-backed **P3SC shader declaration**.

- Only a source material declaring `CF_COLORMAP` may attempt original-derived color texture preview.
- The chosen source texture must match its original C5 P3MR/P3SC references.
- If the source material has **two different texture references**, the renderer keeps the original geometry **untextured**, instead of guessing the color slot from filenames. A single non-sentinel referenced texture is allowed as a *conservative preview candidate*, **not** claimed to reproduce the 3DS GPU sampler behavior exactly.
- Missing, truncated, corrupt, wrong-model or malformed P3SC files never enable guessed textures.
- Actual GPU sampler roles, shader effects, UV transforms, and source color parity remain unverified. This milestone has no impact on high-detail P3CS's intentionally untextured source chunks.

The private release gate requires per-model CRC-valid original shader declaration sidecars and still denies release on other outstanding feature-parity requirements.

## Synthetic tests and remaining work

`sh tests/run_c110_shader_caps.sh` compiles and exercises the exact native C5 shader metadata loader and C109 texture-reference gate, including two-slot ambiguity, absent colormap declaration, missing textures, model mismatch, malformed CRC, short/extra records, and zero stale-ready-state after failures. The Python suite generates C110 sidecars from synthetic source C5/C75 fixtures, proves a shader declaration is **not** a confirmed GPU sampler, and rejects a partial 730-model inventory. Tests are part of `make check-host`.

The full original shader/sampler decode, proprietary shader color selection, original animation/audio, full challenges, source-accurate interfaces, and private-asset melonDS/hardware screenshots remain incomplete. Do not call this game or its visuals finished.
