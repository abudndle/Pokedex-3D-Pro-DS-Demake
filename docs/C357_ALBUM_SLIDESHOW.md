# C357 Album slideshow DS adaptation

Advances the missing Album slideshow flow under #227 / #301. While a valid
photo is open, A or the visible touchscreen play/pause row toggles playback.
The DS adaptation uses 300 VBlanks (about five seconds) per photo. It advances
through descending canonical filenames, crosses list pages, and loops from
oldest to newest. Manual Left/Right browsing pauses and resets the dwell.
B returns to the selected list row. A missing/current or invalid next file
stops autoplay, with no automatic retries or writes to source media.

Opening, closing or restoring a photo resets playback to paused. Existing
C356 v7 checkpoints continue storing only the current photo identity;
no save-format or private-asset change is introduced. A frame tick performs
no filesystem IO; directory scans and one bounded decode happen at advance.

The original 3DS timing, transition effects and slideshow artwork have not
been source-verified. This is playable DS adaptation infrastructure, not a
claim of original-game timing or full Album parity. Camera/associations,
original visuals and physical DS/DSi remain unfinished.

Tests: `sh tests/run_c357_slideshow.sh` exercises actual PNG decoding, timer
boundaries, pause, looping, cross-page advance, restore-paused semantics and
corrupt-file stop. An independent Python check verifies source media bytes.
The initial absent API could not compile (not counted as red); with inert
API scaffolding the same command compiled and failed its first Play assertion.
The implemented command passed. The C268 workflow adds actual melonDS timed
button/touch playback, pause holds, manual browse, reboot and FAT validation.
Synthetic PNGs only; CI/runtime acceptance pending at initial publication.
