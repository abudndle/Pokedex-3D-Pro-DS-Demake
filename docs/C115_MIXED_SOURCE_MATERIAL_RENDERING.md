# C115 — Preserve Pokémon geometry with mixed source-backed and unresolved materials

## Goal

The target is a **complete port of the original 3DS Pokédex 3D Pro**, with the **original title screen unchanged** and the authentic rest of the interface, original Pokémon models/animations, audio, controls and gameplay. The original private assets must never be committed to public GitHub.

## Native rendering milestone

Earlier C107–C114 validation required all material ranges in a Pokémon model to be compatible with the same conservative simple-colormap preview. One original C5 material declaring `CF_BUMPMAP`, another effect, or more than one distinct source texture could disable **all** model textures even when other original materials were source-backed simple-color candidates.

C115 adds a **per-original-material-range eligibility map**:

- The mesh's complete P3MT/P3TX triangle coverage, original source C5 P3MR draw material indices and texture references, original C5 P3SC shader declarations and P3SW 13-word operation records must still agree. A missing or contradictory source sidecar fails closed.
- A range qualifies for a DS *preview candidate* **only** if its original shader has `CF_COLORMAP` and **no** bump or other undecrypted original shader capability, and it references exactly one distinct source texture ID matching its material. A single source reference is **not** proof the GPU color role is fully decoded.
- Other ranges, including original bump/effect/dual-sampler cases, **stay untextured** with the original model geometry and any available verified face colors. All original triangles are drawn once in source order, not skipped.
- The upload path receives this range map, allocates VRAM only for distinct qualifying textures, and does not even read blocked source P3PX files. Failure of **any approved texture** still cleans up all uploaded textures and uses an all-untextured geometry fallback. The existing **128 KiB / eight-texture DS limit** remains.
- If the source geometry is a high-detail P3CS chunk model, it remains entirely untextured while original GPU shader equations have not been verified. This milestone does not fabricate extra original gameplay or art.

## Synthetic regression coverage

`tests/run_c110_shader_caps.sh` now also compiles the real `source_color_ranges.c` implementation and exercises original C5 mixed-material cases: all simple-color source spans eligible, color+bump excluded without excluding a separate simple span, color+unknown-effect excluded, all excluded, bad candidate references, wrong model triangle count and null output.

`tests/run_c108_material_binding.sh` tests the *actual native upload* implementation with a partially approved material map and a deliberately corrupted **unapproved** texture file. Only the approved original-derived synthetic texture uploads; excluded corrupt data is never loaded. Empty, malformed and wrong-length maps fail without allocation. Existing tests still check memory budgets and cleanup on upload failures.

Both tests run in `make check-host`. BlocksDS CI and an asset-free DeSmuME smoke ROM check build/startup, but **do not verify original 3DS rendered appearance**.

## Still blocked

The actual source 3DS GPU sampler roles, original bump/normal/specular/effect equations and texture-coordinate transformations are not decoded. Native mixed-material preview is a **conservative diagnostic**, not finished reproduction of original shaders. Full original title-screen **visual parity** and all remaining models, audio, animation, menu, settings, challenge and AR/gameplay features still require private original-asset tests and development. No title-screen source or assets are modified by C115.
