# C92 — Source-derived experimental textured model previews

C92 is a **diagnostic** rendering milestone, not completion of the original
Nintendo 3DS Pokémon shaders or all 730 original models.

## Original-data evidence

The user's private C88 material inventory contains 3,473 original material
records. Exactly **2,215** have a canonically named original color texture
(`*Cl_ctr`, `*Cl_cta`, `*Cl_ctb`) in source texture-reference slot 0,
while **zero** contain such a canonical color name in slot 1.

This strong source-data correlation supports a *test candidate* for using
slot 0 as a color sampler. It is NOT independent proof of the original GPU
sampler-channel hardware semantics, source combiners, specular lighting,
emissive effects, transparency modes or normal-map treatment.

The C91 538 model/2,360 sampled-material-range inventory has 78 ranges
without a canonical color-name candidate, across 38 models. The private
C92 review queue classifies these as:

| Source-level exception | Sampled ranges |
|---|---:|
| Normal map with no other referenced texture | 31 |
| Normal + specular, no color name | 13 |
| No texture references, despite a shader flag | 27 |
| Noncanonical/other texture names | 7 |

Those 38 models are excluded from the private experimental staging archive
rather than silently borrowing the first texture or a texture from another
Pokémon. Some flagged materials may intentionally be untextured effects.

## Private **experimental** model ZIP

The user's private C92 archive has **3,153 ZIP members**, all under
`diagnostic_nitrofs/` except an explicit warning README. It contains, for
**500 models**, the exact matching original-derived C86 geometry/UV sample
pairs, source C90 material-index ranges, candidate color-material P3MT files,
P3TX manifests and **1,152** C91 original-derived A1 RGB555 color textures.

- **2,147** experimental contiguous material-to-color ranges across
  **299,997** sampled source faces (not full original high-poly geometry).
- All matched source geometry/UV data and C90 material-index references were
  cross-checked. Images are exact C91 converted/resized original-derived files.
- Every model uses 8 or fewer distinct color images and no more than
  **128 KiB** of planned preview texture memory.
- **464** of the 500 models require lossy downscaling for the DS preview budget.
- Private ZIP CRC, file headers, geometry/UV counts, material coverage,
  model-local texture IDs and image dimensions checked.
- **Eight** local regression tests passed, including corrupt source CRC, wrong
  model IDs, mismatched triangle counts and out-of-bounds texture budgets.

These are **experimental P3MT maps derived from original source color-NAME
correlation**, not verified original sampler associations. They have the
standard native P3MT/P3TX format specifically to permit controlled *opt-in*
preview comparisons, but **must never be automatically mixed into final
NitroFS output**.

## Reproduce and validate privately

The source-only public archive auditor validates a private C92 preview ZIP:

```sh
python3 tools/c92_diagnostic_textured_preview_audit.py \
  /private/C92_PRIVATE_EXPERIMENTAL_TEXTURED_PREVIEW_NITROFS.zip \
  --require-c92-full-batch
```

The private authoring scripts and detailed per-model diagnostics are included
with the user's C92 private tools and reports package. To test an experimental
preview, deliberately extract `diagnostic_nitrofs/` into a *separate private
test project*. Do not use it for a normal release, and do not upload any
Nintendo-derived game assets into this public repository.

## Remaining original-game fidelity blockers

- Independently decode the actual 3DS GPU texture unit / channel roles and
  blending/shadow/environment combiner semantics.
- Resolve the 38 exceptional original-material cases above and the 162
  partial-UV models; recover 26 missing full UV exports and four absent C7
  texture groups/model previews.
- Compare rendered source-model preview screenshots with the user's lawful
  original game captures and confirm real DS/DSi memory/hardware behavior.
- Finish missing original animations, audio, remaining challenges and
  original-language/localization and camera/touch features.

The **C85 original-game final-build release gate remains blocked**. A
successful source-only GitHub ROM build is not evidence these experimental
models match the original game.
