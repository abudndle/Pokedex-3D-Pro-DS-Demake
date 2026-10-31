# C88 — Original C5 material reference recovery (730/730)

## Verified result from the user's private original model archives

A cross-model table structure was validated using original C56 decoded C5 buffers and original C75 texture-name pointers:

- **730 model records examined, no structural errors**
- **3,473 original named materials**, each with an in-range source shader index
- **2,556 original shader definitions** referenced through independently bounded source tables
- **4,592 source texture-reference slots** tied to verified original C75 texture names
- **2,260 two-texture material records**, **1,105 records with no texture references** and **108 single/special records**
- **726 models** have the archived original C75 texture names; four additional original decoded C5 models (`p730`–`p733`) have source material/texture indices but do not yet have C75 texture archive images
- **0 verified original mesh-to-material face ranges**. Do not fabricate them.

## C5 structure independently validated

Source header `<H` at `0x0c`, `0x0e`, and `0x10` contains source shader, texture and material counts. Four `<I` section offsets at `0x2c` identify the 8-byte shader table, 28-byte texture descriptor table, 52-byte material table and following bone section. All 730 recovered model headers have exactly matching table lengths/boundaries.

Within each 52-byte original material record, low 16 bits of word 0 index its source shader declaration; low/high 16 bits of word 1 are two **source texture indices**, with `0xffff` meaning no reference; low 16 bits of word 8 is the original material-name string offset. All offsets/indexes were validated in range and, for the 726 models with C75 archives, every original texture-name pointer was byte-checked against C5. Upper bits and sampler roles remain opaque.

For example, in recovered source model `p000` (Bulbasaur):
- `BodyA` and `BodyB` reference the original `Fushigidane_bodyCl_ctr` and `Fushigidane_bodyNorOS_ctr` texture entries.
- `Eye` references `Fushigidane_eyeCl_ctr` and `Fushigidane_eyeNorOS_ctr`.
- `shadow_w` points to a shadow shader, with no source texture references in the two decoded slots.

This is original **material-to-shader and material-to-texture index linkage**, not merely fuzzy texture-name matching.

## Run privately

```sh
python3 tools/c88_original_material_references.py \
  --source-dir /private/C56_archives \
  --texture-reference-csv /private/C75_ORIGINAL_TEXTURE_DESCRIPTOR_NAMES.csv \
  --report /private/C88_original_material_refs.json
```

Keep C5 model buffers, original names, C75 CSV, original texture pixels, and detailed derived tables privately. The public repository contains only the clean parser, synthetic tests and non-payload documentation.

## What is still blocked

C88 **does not** know which per-triangle face ranges select each original source material. We must establish source mesh-to-material references and preserve source polygon order before generating real `P3MT` material ranges. We also need to recover missing original pixel textures for four source records, handle partial UVs, fit DS VRAM and compare original-looking models on actual emulator captures. Source texture pair order is not yet a proven GPU sampler-channel mapping; never upload normal/bump textures as diffuse maps based on string patterns alone.

The existing C85 final-release blocker remains in place.
