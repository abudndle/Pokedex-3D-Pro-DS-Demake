# C119 — Resume last screen, persistent AR Viewer icon, and Pokémon title-idle scene

## Original game behavior requested

The final Nintendo DS/DSi port must include **all** original Pokédex 3D Pro screens and assets: Pokédex, Move Dex, Pokémon Challenge, Records, Album, AR Viewer, Settings, and the original icon art and navigation. The **original 3DS title screen** remains mandatory. If left idle, the title's upper display changes to a Pokémon scene linked to the last visited/saved Pokémon, shows the console's actual **weekday, date, and time**, and asks the player to check that Pokémon's Pokédex entry.

## Implemented in native C119

- **Resume:** A separate dual-slot `P3RV` save stores HOME/page, selected Pokédex and Move Dex indices, active menu highlight, record tab, and Album page. Each 32-byte record has a version, sequence number, CRC32 and strict bounds. If the latest record is damaged the prior valid slot is restored. Existing P3SV/P3RC saves remain compatible, and absent P3RV data leaves the normal boot state.
- **Automatic checkpoint:** While writable FAT/DLDI storage is available, the game periodically flushes changed page/selection and progress after a 60-VBlank interval, as well as on existing explicit saves. The DS cannot reliably trap a hard power-off or cartridge removal, so this is bounded periodic persistence rather than an untrue guarantee to save at the instant power is removed. When no writable storage is available, the save does not falsely claim success.
- **Resume after title:** The title's first ordinary A/START/touch transitions to the previous active page if it was saved; on first run it goes to the usual HOME state. It never forwards the same input into another menu item. If the previous page requires unsupported DSi camera hardware, it safely falls back to HOME.
- **Menu gating:** The AR Viewer stays present in the menu on DS and DSi instead of disappearing. Entry is blocked when the DSi camera backend is unavailable. The text fallback labels it `[DSi camera only]`; original icon artwork is still loaded through the private source-derived HOME graphics, not redrawn or fabricated. Hardware DSi-mode detection uses `isDSiMode()`, but an unfinished camera backend is not falsely marked working.
- **Title idle preview:** After 720 DS VBlanks (~12 seconds of inactivity), the **top screen** changes from original title art to a preview of the last saved/visited Pokémon **when real source geometry is available**, with a textual prompt and clock date/time/weekday read using libnds-compatible `time()`/`localtime()`. **A** in idle mode opens that Pokémon's Pokédex entry. B/START/touch resumes the previous screen. The **bottom screen** continues displaying the original recovered title image. The original title's optional animation and sound cues remain on the normal non-idle title; no unknown 3DS sequence, original overlay glyph, or transition effect is invented.
- **Safety:** If source model/texture assets or storage are absent, the development build shows a limited text/scene fallback rather than making up original assets. The private original artwork and exact original idle-scene animations/compositing have **not** been supplied or visually verified.

## Tests

`tests/run_c119_resume_idle.sh` verifies two-slot write/restore, corrupt newest-slot rollback, exact page and selected Pokémon/move recovery, no resume into unsupported AR, no invalid-page persistence, title-idle threshold and real-system clock formatting. Existing feature-menu/DSi tests now require AR to be *visible* while disabled on unavailable hardware. Source checks, host tests, a BlocksDS development ROM build and an asset-free DeSmuME smoke test are required before merge.

## Incomplete original-game parity

The original HOME **icon hitboxes**, exact order/layout, original greyed AR icon sprites, all settings and source 3DS transition timing, full original title idle scene background and genuine idle motion, 3DS visual fidelity, complete camera-backed DSi AR, full music/cries, models and all gameplay still require private source integration and verification. Do not describe the original game as fully ported.
