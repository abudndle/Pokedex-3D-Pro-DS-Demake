# C121 — Full in-screen resume context and backward-compatible P3RV v2

## Requirement

Pokédex 3D Pro on DS/DSi should restart on the **actual last page and its last in-page state**, not merely return to a title screen or reset the current Pokémon form, album cursor or Move Dex text position. The original Nintendo 3DS title screen and all gameplay features remain the full-port requirement. This milestone does not claim original visual parity or original save-format compatibility.

## Implemented

- Extends existing private DS checkpoint **P3RV** from **v1 (32 bytes)** to **v2 (48 bytes)**, retaining the same dual `_resume_A.sav` / `_resume_B.sav` file names and monotonically incremented 32-bit sequence numbers.
- Reads both **original C119/C120 P3RV v1** 32-byte files *and* C121 P3RV v2 files in each slot. V1 records decode with all newly introduced state set to safe defaults. The first new save migrates to v2 **in the alternate slot**, keeping the valid v1 record available as rollback if the upgrade write fails or is corrupted.
- Preserves previous page/HOME, main icon highlight, Records tab, Pokédex species, Move Dex index, Search Pokémon selection and Album page, plus **selected Pokémon alternate form**, **selected Album thumbnail**, **Records recent-Pokémon cursor**, **Move Dex effect/description view and text scroll**, **Search region/scope/field**, the menu's subcursor and the Favorites cursor.
- Validates all new byte fields independently of file CRC and rejects corrupt versions, reserved bytes, wrong lengths, invalid indices and wrong checksums. A valid alternate slot still restores the previous screen when the newest fails.
- On boot, alternative Pokémon forms are restored only if the **original private P3FM form-to-model mapping** contains the saved species/form; otherwise it safely uses the base form, not a synthetic one. Deleted album pictures invalidate the old selection safely, stale Records cursors are reset, and the Move Dex text scroll is clamped to the actually available private source text.
- P3RV remains independent from original DS progress P3SV/P3RC; **a valid checkpoint resumes the saved screen directly after reset**. A fresh boot without a valid checkpoint continues through the original title-screen loader if private original source art exists.
- Original C120 title idle picks any Pokémon independently; an idle scene never overwrites the saved form/page, and its A prompt opens the displayed Pokémon.

## Binary format

Both versions begin with `P3RV`, version (uint8), three reserved zero bytes, sequence (uint32 LE), and the original 12-byte main-screen record. V1 has four reserved zero bytes followed by CRC32 at offset 28. V2 uses bytes 24–36 for alternate form, Album selection, Records cursor, Move effect/description flag, search filter settings, Move text position, subcursor and Favorites cursor; bytes 37–43 are reserved zero and CRC32 is at offset 44. All files must terminate at the exact corresponding version length.

## Tests and limitations

`tests/run_c121_deep_resume.sh` compiles the real native C save parser and verifies v2 context round-trip, on-reset restored page/cursor, bounds validation, correct-CRC but invalid in-screen state, previous-slot fallback, original 32-byte C119 format loading, and v1 → v2 upgrade/rollback. The prior C119/C120 reset and title idle tests remain required.

Full original 3DS save-file binary compatibility is not established, nor are all hidden game submenus or transient settings restored. Since DS/DSi cannot trap hard power loss, an interrupted FAT write can still lose the newest checkpoint; a previous valid checkpoint survives. The original 3DS title artwork/animations, original shaders and game content are still private and require real visual/gameplay verification.
