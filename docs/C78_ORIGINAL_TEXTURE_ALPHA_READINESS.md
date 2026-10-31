# C77/C78 — original-derived DS texture conversion

- C77 converted 3,251 fully opaque original-derived C7 textures to P3PX v1, deferred 788 with any non-255 source alpha.
- C78 converted all **4,039** recovered C7 textures from **726** model records to P3PX **v2** with original-derived color bits and 1-bit alpha. **756** have transparent pixels using threshold 128; **783** contained partially translucent source pixels and therefore lose intermediate alpha.
- P3PX v2: `P3PX`, LE16 version=2, width LE16, height LE16, followed by width*height LE16 direct-color texels. Bit 15 is opacity; zero transparent, one opaque. The DS GL_RGB direct-color upload handles the pixel bits.
- Private ZIP layout: `textures/pNNN/tIII.p3px`. The native viewer selects this *per-resource* folder to prevent texture index collisions between distinct Pokémon.
- The model material map (`nitro:/materials/pNNN.p3mt`), texture manifest (`.p3tx`) and verified UV (`.p3uv`) **must still be supplied** for the renderer to attempt textured rendering. Their bindings are **not** inferred or fabricated by this change.
- Original model texture names do not prove body/eye/FX mesh assignments. Source C7 RGB555 may be provisional; normal maps and effect sources must not automatically be applied as color maps. C78 does not claim complete visual fidelity or 730 finished models.
- Existing native texture limits remain at eight distinct textures and 128 KiB of budget; do not upload entire original texture sets at once.
- Original texture archives, game dumps, converted P3PX packs, screenshots and source-derived meshes are **private**. Never put them in this public repository.

Local converter and manifest: `c78_restore_ds_transparency.py`, `C78_TEXTURE_ATLAS_STATUS.csv`, `C78_MODEL_APPEARANCE_READINESS.csv`, and private ZIP are kept outside public GitHub. No copyrighted assets are committed here.
