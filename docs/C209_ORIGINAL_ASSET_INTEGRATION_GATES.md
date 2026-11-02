# C209 — Original asset integration gates

The final port must include all original Pokédex 3D Pro features and verified original resources, but **none of the original commercial assets are committed to this public repository**. This file records executable integration prerequisites rather than claiming completion.

## Local authorized resource staging

1. Place authorized extracted C5/C56/C62/C63/C84/C86/C98/C148 archives and sidecars in a **private directory outside the repository**. Never commit them or their derived original geometry, screenshots, manifests, or content hashes.
2. Validate archive provenance, inventory, and bounded extraction with existing private recovery tools. The previously reported 730 C5 models, 528 complete and 162 partial UV exports, and 730 skeletons are **historical recovery counts**, not verified renderable DS models.
3. For each model, produce a P3VX stream only from uniquely source-matched XYZ records using `tools/c207_private_c5_xyz.py`. Independently prove matching P3IX topology; do not infer triangles from the OBJ without evidence.
4. Run `tools/c183_private_geometry_batch.py` with a compiled native probe. Its private report distinguishes native pair verification from original-source provenance and private-asset emulator verification.
5. Reconcile C5 material and sampler IDs with C84/C86 texture data, mesh partitioning, skeleton nodes and animation tracks before claiming authentic rendering. A geometry-only success does not satisfy this requirement.
6. Stage the asset-integrated NitroFS manifest in the private workspace, then run `tools/validate_original_assets.py`. The public CI uses synthetic fixtures only.

## Completion evidence matrix

| Gate | Required evidence | Current claim |
| --- | --- | --- |
| Original C5 model provenance | Per-model descriptor/geometry identity and exact original ownership | Partial private recovery; not 730 proven complete |
| P3VX/P3IX native geometry | Paired valid streams, native loader probe and draw result | Synthetic regression path implemented; full private batch not proven |
| Original texture/material mapping | Verified mesh-to-texture/sampler bindings and rendered visual comparisons | Incomplete |
| Original skeleton/animation | Owner-to-node and pose playback verified against original | Incomplete |
| DS ROM | Reproducible BlocksDS build, saved output and emulator smoke | Asset-free smoke build available; not original parity |
| Original UI and all game features | Visual and functional acceptance tests for every screen and mode | Incomplete |
| DSi AR camera | Hardware-capability gating, capture and AR gameplay verification | Incomplete |

## Next executable milestone

**C210 should validate model-specific mesh index bounds** from decoded P3VX mesh tables against P3IX index values, rather than relying solely on global vertex capacity. It should use the actual native loader's mesh-local index semantics and synthetic C/Python regression fixtures. Do not reject valid original triangle data based on guessed limits.

For every new milestone, commit implementation plus regression tests, run source and native ROM workflows, and merge only after the relevant checks pass.
