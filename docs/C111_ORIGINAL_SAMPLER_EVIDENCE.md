# C111 — Original 3DS C5 GPU material-word evidence and safe sampler guard

## Goal and original-game fidelity

The target remains a complete **Pokédex 3D Pro (Nintendo 3DS) port to Nintendo DS/DSi**, retaining the original appearance on both screens, all models, original menus, motion, sounds, data, and gameplay. No inferred replacement artwork or Pokémon shaders may be described as the original game.

C110 recovered the original shader *declaration* bits `CF_COLORMAP` and `CF_BUMPMAP`, but **a shader capability is not a decoded GPU texture sampler equation**. Source C5 material records contain 13 raw 32-bit fields, some of whose sampler-operation meanings are not decoded. C111 adds an evidence-preserving private inventory, NOT a fabricated sampler-role map.

## Private source audit

`tools/c111_original_sampler_evidence.py` accepts the user's own three private decoded C5 archives and the original C75 texture-name CSV, reusing C88's original pointer, source material, shader and texture validation.

It records each recovered source material's **exact 13 little-endian material words**, material index, original shader declaration, both actual source texture-reference IDs, original-material SHA-256, and whole-source C5 SHA-256. The original records remain in a **private-only evidence ZIP**. Each material is classified into a conservative category:

- No `CF_COLORMAP` declaration
- `CF_COLORMAP` with `CF_BUMPMAP`: unresolved original GPU operations
- `CF_COLORMAP` with multiple distinct / missing source texture IDs: unresolved
- `CF_COLORMAP` with one source texture and no `CF_BUMPMAP`: **candidate only**, not verified final color sampler

The summary explicitly reports **zero verified GPU color and normal sampler roles** and `release_ready: false`. Never use this report by itself to generate P3MT texture-color assignments, assert shader fidelity, or publish proprietary game content. This is evidence for the next investigation into C5 shader instructions, not invented diffuse-color mappings.

With privately owned decrypted assets staged on a local computer, invoke:

`python3 tools/c111_original_sampler_evidence.py --private-root PRIVATE_C5_FOLDER --texture-reference-csv PRIVATE_C75_NAMES.csv --output PRIVATE_C111_SAMPLER_EVIDENCE.zip --require-full`

`--require-full` rejects an archive missing any of the 730 expected C5 resources. In the current public repository the original private C5 archive bytes are **not available**, so full-source verification remains incomplete.

## Native renderer change

C111 tightens the C110 native texture gate. A C5 shader declaring both `CF_COLORMAP` and `CF_BUMPMAP` is **not** treated as a proven color-only texture even with one original texture reference. The native DS preview refuses to assign a color texture to this ambiguous material and renders the Pokémon geometry untextured. This continues the C108 geometry, C109 original material reference, and C110 shader-capability verification without inventing GPU sampler roles. The high-detail P3CS renderer likewise remains untextured until source-verified bindings are available.

## Tests and remaining limitations

`python3 -m unittest discover -s tests -p 'test_c111_original_sampler_evidence.py' -v` verifies source-word preservation, mixed original color/bump flags, single- and dual-reference classifications, SHA-256 metadata, private archive completeness, invalid original C5 shader references, C75 pointer corruption and partial 730-model rejection. The native host `tests/test_c110_shader_caps.c` now covers the mixed color+bump denial.

No original source archive or proprietary data is added to GitHub. Public BlocksDS/DeSmuME smoke tests remain asset-free, and **do not** prove an original-material rendering match. Future work must decode the true GPU sampler and texture coordinate operations, validate original shader behavior with private reference screenshots, restore textures/animations/audio, and complete the original UI and gameplay.
