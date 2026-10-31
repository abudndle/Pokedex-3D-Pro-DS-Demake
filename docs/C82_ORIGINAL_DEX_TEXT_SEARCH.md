# C82 — Recovered original-English Pokédex text and search

## Private source provenance

The user's recovered C18 archive contains `nitrofs/data/dex_en.p3dx`, exactly **166,152 bytes**: an 8-byte P3DX header (version=1, count=649) and 649 fixed 256-byte records (name, description, height, weight). The asset is privately staged as `data/dex_en.p3dx` for NitroFS; do **not** commit original game text to GitHub.

The native C82 loader verifies magic, count, version **and exact file size**. The viewer shows original-English name, Pokédex description, height and weight only if this private asset validates. Missing original data is not silently fabricated.

## Search support

Portable source-language search supports:
- Case-insensitive name prefix and description substring matches
- National, Kanto, Johto, Hoenn, Sinnoh, and Unova regional bounds
- Restrict results to viewed species from C81 Records or six stored favorites
- Bounded 12-character query helpers and next/previous match wrapping

The current native Search screen retains numeric browsing, favorites (X), moves (L), settings (R) and opening a selected Pokémon (A). When English P3DX is available, **X+UP/DOWN** changes the first-letter query and **X+LEFT/RIGHT** searches original Pokémon names. This is a useful keyboard-accessible baseline, not a full original touchscreen keyboard.

## Verification

- C82 private P3DX file validated byte-for-byte: 649 nonempty source-derived names, correct file length and header, ZIP CRC pass.
- Host regression generates a synthetic 649-record P3DX, tests valid and truncated file checks, names, region filtering, description substring matches, viewed/favorite scoping, and rejects invalid scopes.
- C79 private model-texture manifest builder is restored on this branch after PR #49 became unmergeable following the later C80 merge.

## Unfinished

Original text in six other game languages, full evolution/stat/ability/move data, source menu graphics and touchscreen controls, 29 other original Challenge modes, all-model authentic mesh-material bindings, sound/cries and DSi-only AR remain unverified or unimplemented. A BlocksDS CI smoke ROM cannot substitute for a visual melonDS/hardware playtest.
