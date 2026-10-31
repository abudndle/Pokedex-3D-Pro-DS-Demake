# C87 — Recovered original C5 material/shader declarations across all 730 models

The private decoded C56 C5 archives each contain a source string pool with original shader capability labels and original texture-name strings. C87 confirms them by parsing bytes in bounds, comparing the 4,039 original C75 source texture-name pointers to the actual C5 data, and keeping all extracted payloads/private reports out of public source control.

## Verified private batch findings

| Category | Result |
|---|---:|
| Decoded C5 model resource records checked | 730/730 |
| Source shader strings found | 2,556 |
| Models containing source shader descriptions | 730 |
| Source texture name pointers cross-checked | 4,039 |
| Material shader label `kawa` occurrences | 1,826 |
| Shadow label occurrences | 730 |
| Declarations including source `CF_BUMPMAP` | 1,505 |
| Declarations including `CF_COLORMAP` | 1,818 |
| Declarations including `CF_SPECMAP` | 1,405 |
| Declarations including `CF_UVANIM` | 710 |
| Declarations including `CF_ABLEND` | 216 |
| Verified original mesh-to-material bindings | **0** |
| Verified original mesh-to-texture bindings | **0** |
| Structural errors | 0 |

Original texture name patterns produce only **channel hints**. Source textures include 1,665 color-map candidates, 1,594 normal-map candidates, 31 specular candidates, 90 environment candidates, 623 effect candidates, and 36 still-unknown channels. These are NOT authoritative per-material GPU sampler assignments. The DS cannot automatically apply `NorOS` normal textures as if they were color maps.

All seven local Python regression tests passed. The repository also includes independent synthetic regression coverage and private-data-free code.

## Repeatable private batch scan

```sh
python3 tools/c87_original_material_declaration_audit.py \
  --source-dir /private/recovered_C56_archives \
  --texture-names-csv /private/C75_ORIGINAL_TEXTURE_DESCRIPTOR_NAMES.csv \
  --output-report /private/C87_REPORT.json
```

The scan requires the user's private original-data sources; **never** check them in to this public repository. The output is an evidence report, not a ready-made original GPU shader or material renderer. No C87 step modifies `P3MT` or guesses original triangle material ranges. All 162 models with partial source UVs and 26 with no full-UV source export remain unresolved.

## Next technical blockers

1. Decode the actual C5 mesh/material reference table, proving which shader instance applies to each mesh and which original texture IDs are bound to its sampler slots.
2. Reconstruct missing UV faces only from original data and verify geometry order, not by interpolation or using another model's UVs.
3. Build a DS VRAM-safe textured-material selection and test real screenshots against original gameplay; expand original data, challenges, audio and AR separately.

The C85 final-release gate stays blocked. A successful source-only CI ROM or emulator smoke test is not a finished game.
