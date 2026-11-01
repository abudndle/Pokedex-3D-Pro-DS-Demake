# C122 — Source-aware navigation resume and legacy P3RV v1/v2 migrations

## Goal

After the Nintendo DS game resets, reopen the last original game screen and preserve the useful in-screen navigation context from the original 3DS Pokédex 3D Pro. Keep the real 3DS title artwork and the independent any-species idle Pokémon feature; do not fabricate source graphics or gameplay to complete missing content.

## Implementation

C122 introduces **P3RV version 3**, an **80-byte** dual-slot, CRC32-checked checkpoint. The existing 32-byte **v1** and 48-byte **v2** records remain readable, and a newly saved record is written to the opposite slot so the older valid checkpoint remains recoverable if a write is interrupted. The previous version's form, album, records and Move Dex information are retained.

New navigation context persisted with C122:

- Search's exact current typed query (up to 12 original capital Latin letters) and selected starting-letter cursor.
- Pokémon Challenge's selected mode/region in the **picker**. This does **not** invent a lost in-progress question or its answer state: after reset the actual challenge picker resumes with the same region when unlocked, clamped to genuinely available modes.
- Type Matchups' attacking type, defending type and optional second defending type.
- The currently selected entry in the Favorites page, independent of the existing favorite-list cursor.

Each new field has a strict native range check before saving and after loading, including canonical NUL padding for text input, 7-mode challenge bounds, 17 game type IDs and selected-favorite index. Correct CRC alone does not make invalid source state acceptable. Older P3RV versions set newly added state to safe defaults. A valid v2 with existing context can be upgraded to v3 while the old checkpoint stays as fallback.

When the last screen is a valid checkpoint, the native ROM still **boots directly to that screen** without forcing a title visit. Source model/form validation and original face/UI private-asset requirements remain unchanged.

## Tests

`tests/run_c122_navigation_resume.sh` verifies exact new field roundtrips, binary offsets/version/CRC, invalid lowercase or unterminated search query, unsupported challenge/type values, CRC-valid corrupt bytes, reserved words, real 48-byte C121 checkpoint upgrade and previous-slot rollback. The prior C119 and C121 regressions still run, updated to expect new writes as P3RV v3 while retaining C119 v1 decoding.

A native BlocksDS development-ROM build and DeSmuME startup checks use **asset-free** screenshots only. The screenshot evidence does **not** show faithful original 3DS graphics. This milestone does not complete all gameplay, actual Pokémon model/material fidelity, DSi camera AR, original title transitions or full 3DS save-format compatibility.
