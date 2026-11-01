# C120 — Any Pokémon in original title idle; direct resume after reset

## Corrected source-game requirements

Pokédex 3D Pro's **original 3DS title-screen idle Pokémon** may be **any species in the Pokédex**, not necessarily a favorite, unlocked, previously viewed, or the Pokémon selected when the game last saved. During title-screen inactivity the upper display should be able to switch between scenes showing different Pokémon, with the console's actual weekday/date/time and a prompt to open the *currently displayed* Pokémon's Pokédex entry.

Also, **resetting/relaunching the game returns directly to the screen the player last used**, instead of requiring them to enter through the title again. The original 3DS title screen remains an essential part of the port for fresh starts and other title uses; it must not be replaced by invented art.

## Implemented

- `source/title_idle.c` implements a lightweight **independent** session-seeded selector for all **649 Pokédex species** (0–648). It never reads or changes `dex_index`, `selected_dex`, progress/favorites, or the saved last-screen checkpoint. Each new idle scene avoids immediately repeating the preceding species. A separate scene timer allows another title Pokémon to appear after 600 DS VBlanks; these timing/selection details are **development placeholders**, not confirmed original 3DS timing or randomization.
- `source/main.c` loads the **idle-specific Pokémon base-form preview** through the existing source-backed original Pokémon asset pipeline. This is kept separate from the user's last selected Pokémon/form and the persistent `P3RV` state. A on the idle prompt opens the currently displayed species's Dex entry. B/START/touch continues to the previously active page without changing which Pokémon was saved. On scene changes, existing model/texture resources are reloaded using normal validation.
- `source/resume_state.c` adds `p3dResumeRestoreBoot`, which validates the independent CRC-checked, dual-slot P3RV checkpoint and applies the last active page and cursor. The main game loads this even if an older progress-file format is missing. When a checkpoint is valid, **startup renders the saved screen directly** rather than showing the title; when absent/corrupted, the normal original title path remains. On each screen/selection change, P3RV is committed immediately when writable FAT/DLDI storage exists; legacy progress and records still have their periodic checkpoint path. If the newest P3RV slot is corrupt, the previous valid screen is restored.
- The original C116–C118 title artwork, animation, and audio contracts remain in place, as do the seven original main feature icons and disabled DS-only AR Viewer.

## Tests

The C119 native regression suite now also verifies the independent C120 selector: seeds can cover all 649 species, no saved Dex entry influences the selected idle Pokémon, scene rotation never immediately repeats a species, and timing/count bounds are respected. It exercises direct reset into Pokédex and Move Dex and restoration from the previous backup slot even when the newest CRC checkpoint is corrupted. Host source checks, BlocksDS native ROM compilation/validation and asset-free DeSmuME startup are required before merge.

## Remaining fidelity limits

The actual original 3DS idle Pokémon sequence, scene-change delay, background, animation and source artwork remain unverified without the user's private original assets. A source geometry file may not exist for every Pokémon in the current asset-free development ROM: in that case, display textual information rather than fake Nintendo models. DS reset/power removal cannot be intercepted in software; persistence means the **last successfully flushed** P3RV page on writable storage. An instantaneous reset before a filesystem write finishes can lose the newest selection. The entire original 3DS game port remains incomplete.
