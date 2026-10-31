# Model restoration status

| Stage | State |
| --- | --- |
| Original indexed model file extraction | 730 recovered |
| C5 decoding | 730 containers decoded, 7 flagged for unusual descriptor layout |
| Whole-model UV export | 528 new renderable UV OBJs (C62) |
| Partial mesh-level UV recovery | 162 extra exports (C63; some incomplete) |
| Verified original material bindings | Not complete |
| Bulbasaur face / forehead spot | Candidate repair, not certified accurate |
| All Pokémon visually verified | Not complete |
| DS-compatible optimized textured models | Not complete |
| Native DS boot test in melonDS | Not verified |

## Quality gates
1. Source geometry/UV byte and index validation.
2. Per-mesh material binding backed by original data.
3. Visual comparison against reference in front/side/back and animated poses.
4. DS hardware rendering budget and display quality checks.
5. Native ROM boot and interaction tests.

Do not represent diagnostics, partial exports or batch decoding as finished textured models.
