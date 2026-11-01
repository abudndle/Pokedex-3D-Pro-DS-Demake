# C108 — Exact original mesh-to-material binding checks

## Aim

Pokédex 3D Pro's authentic original Pokémon material/UV bindings must match the geometry used by the Nintendo DS renderer. C107 preserved original-derived texture alpha but source ID existence alone was insufficient to validate that every triangle has the correct material assignment.

## Native C changes

- Validate all material ranges are **nonempty and contiguous**, with no gaps or overlaps.
- Reject out-of-bound material/texture array counts, duplicate or unordered texture IDs, wrong texture formats, and invalid texture dimensions.
- Expose p3dModelMaterialTexturesMatchMesh(materials, manifest, mesh_triangles): exact triangle coverage must equal the **currently loaded original-derived preview mesh**.
- Gate native Pokémon texture upload in source/main.c on that exact model coverage check, in addition to existing UV availability and P3PX payload/VRAM checks.
- Continue deduplicating repeated material references to the same texture, and keep the existing 128 KiB texture VRAM / eight-allocation ceiling. If payload loading or GL upload fails, delete all partially allocated textures and render without them.

## Synthetic verification

tests/run_c108_material_binding.sh constructs real P3MT/P3TX/P3UV/P3PX fixture files (no Nintendo content) and compiles the same loaders and real GL upload branch used by the game, with capture-only host GL. It tests material range coverage, per-triangle texture ID, reused references, original alpha format, stale state after failures, invalid/missing pixels, cleanup on second-texture upload failure, and rejection of an over-budget texture set before the first upload.

## Important limitations

This milestone verifies **internal geometry/material/UV agreement**, not whether the experimental recovered P3MT mapping reflects the 3DS GPU's actual original sampler/shader roles. Original GPU source evidence and private per-species rendered comparison are still necessary. In particular, C92 diagnostic color-name-hint mappings are NOT by themselves proven original bindings, and the high-detail P3CS chunk renderer intentionally does not enable unverified materials. Full 3DS visual/gameplay fidelity, animation, audio, touchscreen source hitboxes and asset-bearing melonDS testing remain incomplete.
