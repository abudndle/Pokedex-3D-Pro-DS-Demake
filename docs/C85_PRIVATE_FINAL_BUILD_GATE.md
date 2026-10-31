# C85 — Private full-build gate

A normal `make` is intended to build an original-asset-integrated final DS ROM. It **must now fail** if the required original game assets or end-to-end gameplay parity are incomplete, rather than silently producing a partial game that looks like a release. The asset-free `make dev-rom` continues to build separately through `Makefile.native` for developer diagnostics.

Run a nonblocking private asset audit on a ZIP or extracted NitroFS folder:

```sh
python3 tools/check_private_release_assets.py --root /private/C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip --report /private/C85_AUDIT.json
```

The audit checks ten original-derived UI pages, 649-entry P3DX, 559-entry P3DM seek index, 730 expected C5 model IDs (0–733 except 721–724), DS3M/P3UV/P3MT/P3TX/P3TM model files, and at least 4,039 original-derived P3PX textures.

The current user's **private C84 asset stage** includes the original UI pages, Dex data, 559 moves, texture catalogs and 4,039 original-derived converted pixels, **but not 730 finished DS3M models, verified P3UV for every model or P3MT mesh-material bindings**. Consequently normal final-release `make` intentionally fails. This is correct until the missing originals and associated gameplay are recovered.

`--release` additionally enforces `tools/check_feature_parity.py --release`. That parity check refuses release until all 20 original-game feature areas have verified emulator/hardware evidence. File presence alone must never be treated as proof of authentic model appearance or complete gameplay.

The audit scripts and synthetic tests are public-safe. Commercial game payloads and private extracted assets are not stored in GitHub.
