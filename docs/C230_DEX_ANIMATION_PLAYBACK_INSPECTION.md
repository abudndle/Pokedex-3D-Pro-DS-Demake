# C230 — Text-mode Pokédex animation playback inspection

The native Pokédex can load optional validated P3AN v1/v2 *transform transport* clips. C230 makes those clips inspectable with **Pause/Resume** and **Restart** touch controls, without altering the recovered original-game assets or the 3DS artwork. This is not an original skeletal-animation implementation.

## Native interface

When a valid animation is **actually drawable** in the Pokédex text-mode renderer, console row **12** displays `[Pause]` / `[Resume]` and `[Restart]`, beneath the original species-name row. Tapping the lower-screen rectangle **y=88–95** toggles pause on the left half (x=0–127) or sets the playback tick to zero on the right (x=128–255); restart keeps the existing pause state. SELECT still switches original-art bitmap/text display. When the original bitmap is present, touch controls are hidden and disabled. Existing text-mode entry browsing uses the bottom corners below y=150 and does not overlap.

Changing Pokémon species, form or validated clip resets playback to frame zero and resumes. The title's independently chosen idle Pokémon also uses the same bounded playback counter; no restart/pause hotkey is added to the original title or to other pages. Combining touchscreen contact with another control key does not trigger these playback actions.

## Validation and release boundaries

- `sh tests/run_c230_playback_controls.sh`: synthetic C host test of pause/resume, restart-in-paused-state, last-frame wrapping, even a corrupt UINT_MAX tick, missing/invalid clips, DS coordinate bounds, hidden artwork and source-geometry gates.
- `make check-host`: includes this new regression without any original data.
- `.github/workflows/port-source-tests.yml`: explicitly exercises the regression.
- `make dev-rom` with the existing BlocksDS native workflow: compiles the actual ARM9 event loop and the new module with no proprietary NitroFS payload.
- DeSmuME emulator smoke jobs remain an **asset-free startup** gate, not proof that these private animation clips or accurate 3DS Pokémon skeletons were displayed.

The controller deliberately **refuses to advance or expose animation controls** for private P3VX/P3IX source geometry. That renderer has no independently verified matching skin-weight and motion binding. Original 3DS skeletal animation, matched assets, original playback UI and visual fidelity remain unfinished. No Nintendo source payload, private model, proprietary hash, source-derived animation key or screenshot enters public CI.
