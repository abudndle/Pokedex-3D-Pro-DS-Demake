# C91 — Original-data color-name evidence and DS VRAM feasibility

C91 uses the already-recovered C88 source **material→texture indices** and C90 source **mesh→material indices**, cross-checking the recovered C78 original-derived texture file inventory.

## Verified private batch checkpoint

- **538** recovered complete-UV/source-matched DS3M/P3UV candidates and P3MR source-material sidecars inspected.
- **2,360** sampled source mesh/material ranges examined.
- **2,282** ranges have exactly one **source-name color candidate** with original shader `CF_COLORMAP` capability.
- **78** ranges lack that unambiguous candidate; **38** models remain blocked for original texture sampler verification.
- **500** candidate models have color-name matches for *every* sampled material range, with **1,152** distinct source-derived color texture images.
- **464** of these models need some power-of-two downscaling to fit the current preview path's **128 KiB** VRAM budget. All selected model sets fit after resizing and use at most eight distinct textures.
- **Nine** local Python regression tests and **four** independent source-only audit tests passed.
- The private converter verified each original-derived C78 P3PX against its SHA-256 before generating the 1,152 lower-resolution A1 RGB555 diagnostic files; all package P3PX headers, payload lengths, per-model VRAM sums and ZIP CRCs passed.

The private archive is **diagnostic only**, arranged under `preview_colors/pNNN/tIII.p3px`. It is not a drop-in original material renderer. The source-derived resizes are **lossy**; they are not visually identical to full-resolution 3DS textures.

## Grounding and limitations

Original source texture-name endings like `bodyCl_ctr` and original shader `CF_COLORMAP` flags provide strong **candidate evidence**. They do **not** independently establish which original 3DS GPU sampler unit receives each material's texture index. The unusual C88 material cases using normal, specular, environment and effect maps still require reverse engineering.

**Zero original sampler-channel assignments were marked verified, and zero P3MT diffuse maps were generated.** The shipped renderer must continue to reject unproven texture placement rather than silently decorate the wrong body or eye triangles.

This milestone does not repair 162 partial-UV source models, the 26 other missing complete-UV exports, four missing texture-source groups, all original animations or gameplay features.

## Public-safe reproducibility

```sh
python3 tools/c91_color_name_vram_audit.py \
  --materials /private/C88_ORIGINAL_MATERIAL_REFERENCE_TABLE.csv \
  --textures /private/C78_TEXTURE_ATLAS_STATUS.csv \
  --sidecars /private/C90_PRIVATE_ORIGINAL_MATERIAL_SOURCE_SIDECARS.zip \
  --out /private/C91_SOURCE_COLOR_BUDGET_AUDIT.json
```

The public script only reads privately provided source metadata and writes diagnostic counts; it does not contain or download original assets and **never emits P3MT**. Source-only CI uses synthetic C88/C90/C78 fixtures.

## C92 next technical milestone

Independently establish exact original GPU texture-unit/channel semantics using the recovered material/shader command tables. Verify exceptional cases against original C5 and texture bytes, then create experimental material-specific DS P3MT mappings only where source sampler roles can be proven, and check real model screenshots in an emulator.

The C85 final-game release gate stays blocked until authentic visual and complete gameplay parity are verified.
