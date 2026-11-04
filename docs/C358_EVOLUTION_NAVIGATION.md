# C358 evolution-reference navigation

Advances existing species-detail #337 / full-game #301 flow. The evolution
tab's source-backed rows now show the recovered P3DX target name when available
and accept a tap to open that canonical Pokédex entry. The current species,
selected species and form change together; the evolution tab stays selected.
The existing v5 checkpoint restores the new target and tab after restart.

Navigation validates the complete P3SD record and current species/form identity
before changing any output. Empty, unavailable, invalid or stale records and
out-of-row taps do nothing. Target metadata is reloaded, so missing target
records show the unavailable state rather than the prior species's evolution
list. Existing favorites, ordinary species navigation, tabs, source-art gating,
photo/slideshow features and legacy saves are preserved.

P3SD carries only canonical target IDs, with no target-form or evolution-condition
field. Following a reference opens form0; this does not assert source-confirmed
form transitions, levels, items, branches or gameplay conditions. No external
species database or invented original values are added. Transport-valid records
still require private original-source provenance before fidelity can be claimed.

Tests: `sh tests/run_c358_evolution_navigation.sh` uses the real P3SD loader,
touch navigation and P3RV store/load across two processes; covers two branches,
form reset, ID0/648 bounds, stale species/form, invalid unused branch, empty rows,
pointer alias failure and exact hit bounds. Before implementation, an inert API
scaffold compiled and failed the first navigation assertion. The same command
passed after implementation. `test_c358_evolution_gate.py` rejects wrong target,
form, selected species, tab, unchanged navigation and reset screenshots.

The existing C260 workflow builds synthetic P3SD/P3DX fixtures into an actual
BlocksDS ROM. Its melonDS scenario follows both branches, checks terminal and
unavailable rows are inert, returns to the source via ordinary navigation, and
checks actual FAT checkpoints and dual-screen continuity after reboot.
Initial-publication status: implemented/unverified, independent CI pending.
Original data, exact 3DS visuals/conditions and physical DS/DSi remain unverified.
