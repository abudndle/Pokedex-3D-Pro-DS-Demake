# C81 — Recovered original Records module integrated with the DS port

Recovered the portable `records.c`/`records.h` source from the user's C18 private source archive. All code committed here is clean source, not original commercial asset data.

## Features implemented
- Viewed/unviewed bitset for all **649 species**, counting the five source-game regions (Kanto 151, Johto 100, Hoenn 135, Sinnoh 107, Unova 156).
- Eight most recently opened entries, ordered newest first, without duplicates. Records tab allows selecting a recent Pokémon and opening the existing Pokédex viewer.
- Seven **currently implemented** Challenge modes: completed counts and highest score in each mode. More original challenge modes still need porting; this is not full game parity.
- Native dual-screen Records tabs (regional totals, recent Pokémon and challenge scores).
- Records updates occur on actual Pokédex page display and on completed ten-question Challenge sessions. Opening the home menu does **not** mark a species seen.
- Automatic save attempt when leaving the current game page, or START retry after a failure, using existing `progress_dirty` handling. Records history uses `records_dirty` and does not clear the dirty bit if P3RC writing fails.
- Independent P3RC dual-slot A/B, fixed-width 160-byte format with CRC32 and a rolling sequence counter, retaining legacy P3SV data and supporting interrupted-write recovery. Missing/corrupt P3RC files reset cleanly on boot without preventing legacy progress loads.

## Verification
Host C regression validates all species counts, regional totals, recent recency, seven-mode score handling, slot CRC fallback and P3SV compatibility. CI source checks and asset-free BlocksDS ARM9 native ROM smoke tests are distinct from emulator/hardware validation.

## Remaining
The original 36 challenge modes (versus seven now implemented), source records screen visual/touch parity, detailed Pokémon data, model material associations, original music/cries, localization and DSi-only camera AR are unfinished. Per-mode records here should never be presented as highscores for unimplemented challenge modes. Never claim release complete while `python3 tools/check_feature_parity.py --release` fails.
