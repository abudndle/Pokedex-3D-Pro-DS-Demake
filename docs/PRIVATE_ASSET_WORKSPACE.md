# Private recovered-asset workspace (C18–C98)

This public GitHub repository contains the **source workflow and inventory**, not Nintendo-derived original artwork, models, binaries, or a complete release ROM.

The following archives were located in the project's owner's private ChatGPT file Library on 2026-11-01. They are **not included in Git**, and GitHub Actions' asset-free development ROM cannot render their contents. Keep all packages local/private.

| Recovery | Exact private archive name | Contents / caveat |
|---|---|---|
| C18 | `Pokedex3D_C18_Forms_Models_Provisional_Color_Source.zip` | 726 C18 preview geometry samples; 14 guessed per-face colors are provisional |
| C56 | `Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip` | Original decoded C5 model resources, part 1 |
| C56 | `Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip` | Original decoded C5 model resources, part 2 |
| C56 | `Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip` | Original decoded C5 model resources, part 3 |
| C56 | `Pokedex3D_C56_Decoder_Tools_and_Validation.zip` | Decoder/recovery scripts and validation records |
| C62 | `Pokedex3D_C62_528_UV_Model_Exports.zip` | 528 source-derived UV-equipped OBJ model exports |
| C63 | `Pokedex3D_C63_Partial_UV_Recovery_162_Models.zip` | 162 further **partial** UV model exports |
| C84 | `C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip` | Original-derived GUI, 559 moves, 649 English Dex entries, 4,039 texture files; incomplete fidelity |
| C86 | `C86_PRIVATE_DS_GEOMETRY_AND_UV_CANDIDATES.zip` | Preview geometry and separately staged UV candidates |
| C86 | `C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip` | Private C84 + 726 C18 fallback model previews, **not** verified material binding |
| C98 | `C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip` | Private legacy vs. source-chunked model comparison NitroFS package |
| C98 | `C98_PRIVATE_TOOLS_AND_AUDITS.zip` | C98 comparison support files and audits |

Also available privately: `C86_DS_MODEL_STAGE_REPORT.json`, `C86_COMBINED_PRIVATE_STAGE_AUDIT.json`, `C98_PRIVATE_GEOMETRY_COMPARISON_VALIDATION.json`, and `C98_PRIVATE_COMPARISON_README.md`.

## Private workspace layout

```text
project/
  private/recovery/     # C18, C56, C62 and C63 ZIP inputs (gitignored)
  private/packages/     # C84, C86 and C98 NitroFS ZIP inputs (gitignored)
  private/reports/      # local analyses, hashes and comparisons (gitignored)
  nitrofs/              # unpacked private asset staging; never commit
  tools/
    c86_batch_ds_geometry_stage.py
    c86_combine_private_nitrofs.py
```

## Rebuild C86 previews and NitroFS locally

These commands operate on **your local private copies**, never on GitHub-hosted original assets. A C7 validated OBJ archive is required by the C86 geometry helper's C7 fallback path.

```sh
mkdir -p private/{recovery,packages,reports}
python3 tools/c86_batch_ds_geometry_stage.py \
  --c18 private/recovery/Pokedex3D_C18_Forms_Models_Provisional_Color_Source.zip \
  --c62 private/recovery/Pokedex3D_C62_528_UV_Model_Exports.zip \
  --c7 private/recovery/Pokedex3D_C7_Validated_Geometry_OBJ_Collection.zip \
  --output private/packages/C86_REBUILT_GEOMETRY_CANDIDATES.zip \
  --report private/reports/C86_REBUILT_GEOMETRY_REPORT.json

python3 tools/c86_combine_private_nitrofs.py \
  --base private/packages/C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip \
  --geom private/packages/C86_REBUILT_GEOMETRY_CANDIDATES.zip \
  --output private/packages/C86_REBUILT_COMBINED_NITROFS.zip \
  --report private/reports/C86_REBUILT_COMBINED_AUDIT.json
```

The 528/162 export figures do **not** imply 690 finished textured Pokémon models. C86's UV candidates require paired source geometry and verified material/shader associations; **do not** automatically promote candidates into production NitroFS. C98 comparison assets likewise do not prove original 3DS visual parity.

## Release and privacy rules

- Never commit any of the listed ZIP files, private staging directories, game dumps, converted Nintendo textures/models or screenshot source art to this public repository.
- Run `python3 tools/check_private_release_assets.py --help` and the repository's tests when preparing an asset-integrated build. Keep missing features as explicit blockers.
- All 649 entries, accurate meshes/textures, source sampler roles, original dual-screen UI, animation/audio, 36 challenges and DSi-only AR still need verification; the port is **unfinished**.
