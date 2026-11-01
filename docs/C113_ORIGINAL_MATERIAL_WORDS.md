# C113 — Original C5 material-operation words integrated into the DS source checks

## Requirement

Port the **complete original Pokédex 3D Pro Nintendo 3DS game** to Nintendo DS/DSi, keeping **the original title screen unchanged** and recreating the other game screens from the owner's private, original Nintendo assets rather than inventing replacement art. Full menus, models, animations, audio and gameplay parity are the end goal, not a cosmetic reference mock-up.

## Original-source evidence instead of guessed GPU sampler routing

Earlier C111 preserved each source C5 material's 13 raw 32-bit words in a private forensic report, without interpreting the unknown GPU sampler fields. C112 now preserves the presence of all source shader capabilities. C113 makes the **full original material-word record** available for native DS validation in a compact private binary sidecar, while deliberately **not** labeling sampler fields with unproven color/normal/specular roles.

The private exporter `tools/c113_private_material_words.py`:
- Cross-checks all original C5 material/shader/texture-reference pointers using C88 and C111 validation against the original C75 name inventory.
- Writes `materials/pNNN.p3sw` inside a **private ZIP**. Each P3SW v1 has a 16-byte header, model resource ID, original material count, reserved word, CRC-32, then **13 original 32-bit words per material, byte for byte**, in source table order.
- Rejects missing or duplicate original models, malformed source pointers, corrupt archives and a partial collection when `--require-full` is requested. Its report states **zero verified GPU sampler roles**, accurately reflecting that the executable C5 shader and original 3DS GPU interpretation still need investigation.
- Does not commit private C5 files, original material operation bytes, shader contents or Nintendo textures to the public project repository.

Example with the game owner's own decoded original C5/C75 data:

`python3 tools/c113_private_material_words.py --private-root PRIVATE_C5_ARCHIVE_FOLDER --texture-reference-csv PRIVATE_C75_NAMES.csv --output PRIVATE_C113_MATERIAL_WORDS.zip --require-full`

Stage private output `materials/pNNN.p3sw` into NitroFS along with the P3MR/P3SC/P3MT/P3TX private assets.

## Native verification, not an invented port

The DS loader `source/source_material_words.c` reads the private P3SW file incrementally, verifies model ID, format, material count, CRC and exact end of file, and clears stale state on failures. This avoids a second large temporary buffer for original materials.

The original material words are **cross-checked independently** against:
- C112 P3SC material shader index and both source texture references
- C109 P3MR original material index / referenced original texture IDs / model triangle count

Only if these agree can the existing C112 conservative color-preview gate be considered. A mismatch renders the existing native Pokémon geometry without guessed textures. P3SW is not a new original GPU shader decoder and does not make the experimental C92 name-derived color assignments authentic.

## Tests and remaining work

The private exporter has Python source fixtures testing the exact 13 original dwords, correct serialization and CRC, corrupt C5 references, source C75 pointers and a required complete roster. The native host regression tests P3SW load, source shader/material join, wrong model, invalid CRC, truncation and correct-CRC mismatched texture references. The private release audit now requires original P3SW data for all 730 model resources, rejects malformed sidecars, and still marks `original_shader_sampler_roles_verified=false`.

Actual GPU sampler/texture coordinate equations, all model shading, original title-screen parity verification, animations, audio, gameplay features and original private-asset melonDS/hardware validation are **not complete**. Asset-free native ROM and DeSmuME smoke tests cannot certify visual parity. No changes to the title-screen rendering or original title-screen assets are part of this milestone.
