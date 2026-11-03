# C289 — native geometry draw preflight contract

The source-verified P3VX/P3IX pair is a geometry-only transport. A valid pair
is not proof of original C5 vertex decoding, UV coordinates, skin weights,
material identity, sampler roles, or animation.

## Acceptance gate

- Require the same resource/model ID for both pair members and reject missing,
  truncated, oversized, corrupt or cross-model files.
- Validate every mesh ID, vertex reference and triangle before opening a native
  GL primitive. Failed preflight must draw **zero** triangles.
- Reset previously loaded geometry on failure and on a species/form change.
- Never attach a P3UV, P3MT, P3MR, P3SC or P3PX payload to P3VX/P3IX by
  matching only a species name, triangle count, or similar appearance.
- Only a separate, independently verified original-source correspondence
  covering **the same ordered triangles and mesh partitions** may authorize
  texture coordinates and source material/sampler mapping. Until such proof
  exists, draw the verified pair untextured.
- Never publish owner-specific SHA manifests, extracted C5 data, Nintendo
  binaries, original screenshots or private NitroFS/ROM artifacts.

## Reproducible asset-free verification

```sh
sh tests/run_c176_native_primitive_draw.sh
sh tests/run_c178_native_geometry_pair.sh
sh tests/run_c289_geometry_draw_preflight.sh
```

The C289 regression exercises a valid source-geometry pair, then injects a
late invalid triangle. The GL mock must observe **no** begin, vertex or end
calls on that failure; recovery must require a new valid draw request.

## Remaining private acceptance

The owner-only C18/C56/C62/C63/C84/C86/C98 archives need a SHA-backed
cross-check of original C5 mesh vertex order, face order, UVs and sampler
identities across all 730 source models. A green synthetic test does not
certify authentic textured Pokémon rendering or original animation.
