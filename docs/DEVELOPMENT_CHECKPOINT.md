# Development checkpoint - 2026-11-06

## Resume point

Current branch: `codex/c401-entry-navigation`, stacked on ready PR #399 (`codex/c400-gameplay-touch-flows`), itself stacked on ready #397. Main inspected remains `b93ed521f953759e5e538049fa4ce08ad8414d2c`.

Previous verified production source: `0cd21f33313c2e06b378d1d9a38c3094be0a6203`. All 24 applicable CI workflows passed. BlocksDS 1.24 rebuilt its private ROM with 151 byte-matching source files. Actual isolated melonDS captures verify Challenge answer/review/footer behavior; a separate authored triangle/P3AN fixture verifies pause/freeze, paused restart and resume. PR #399 is ready and unmerged. Do not repeat these completed slices or the Search fixes in #397.

## New entry-navigation work

Opening a Recent record previously reused A in the destination Dex and could toggle its favorite. Opening a Favorite with X could immediately redirect into Search. Reopening the same bookmarked move could retain its old text offset/effect despite the bookmark requesting the default view.

Explicit entry controllers now consume initiating buttons, synchronize active and selected identities, and reset entry presentation state. Pokemon opens use base form and entry tab; Move opens use the description from offset zero even for the same move. Invalid targets, pages, null or overlapping outputs leave all state untouched. Favorites and the existing menu cursor are preserved. Main handlers use these controllers for Recent records, Favorites and bookmarks; existing ordinary species/move stepping remains unchanged.

Fail-first regressions reproduced stale Records selection and stale same-move context. Native controller, related Move navigation and source smoke checks pass. A dedicated public synthetic melonDS FAT acceptance flow checks Favorite/Recent opens, unchanged favorite data, bookmark viewport/field reset and repeated reboot continuity. Final source-bound CI, build/capture and independent review evidence belongs in the current branch PR; consult it before repeating work. Missing or failing checks block merge.

## Completed implementation carried forward

- Optional paginated source learnsets, exact detail resume and evolution navigation.
- Album PNG viewing, exact photo resume, slideshow controls and distinct visible touch bands.
- Bounded model zoom/reset; Move Dex text-window reset when changing moves.
- Runtime preview-map readiness separate from structural validity and identity verification.
- Readable Records/Types/Move Dex/form/bookmark controls, aligned Search keyboard and clean short queries.
- Shared visible Challenge and optional transform-clip playback rows, with footer safety and original-art gating.

## Original-source and hardware blockers

All 730 native preview structures pass the compiled loader/GL-emission probe. This does not prove all 730 original textured models render. Only one runtime species mapping slot is corroborated; original identity and release readiness remain false.

Complete mapping, missing Japanese/English original loader tables, original UV/material face bindings, skin weights, mesh-node/action semantics, remaining original Challenge modes, audio and full original GUI remain absent or unresolved. DSi camera/AR and hardware behavior need real device evidence. Synthetic animation proof is not original skeletal playback.

Original assets, converted outputs, maps, hashes, manifests, ROMs and screenshots remain outside public source/CI/artifacts. The repository named `-private` reports public visibility; never run proprietary payload CI there.

## Next tasks

1. Read the new branch PR for exact final source and verification results. Integrate this stack only under repository check/approval rules; none of these PRs has been merged or represents full-game completion.
2. Reuse #339 learnsets, #337 original species data, #156/#213 geometry and #227 emulator/hardware acceptance. Keep them open until actual acceptance is met; no duplicate milestones were created.
3. Recover authorized missing original inputs before claiming model/material/animation parity. Advance independent gameplay/save defects while blocked, using fail-first regressions and genuine emulator evidence.
4. Maintain source-bound FAT/restart tests when changing navigation. Explicit entry opens must never reuse their initiating input, silently modify favorites or retain another presentation context.

No original assets were replaced, no milestone was closed, and hardware/full-game parity is not claimed.

Verification follow-up: the first real seven-launch C401 run passed every FAT phase, including both bookmark resets. Its final visual gate exposed a test calibration error: Pokemon 001 to 002 changes a small digit, not an entire text viewport. The gate now requires a real change in the exact species-number field, with independent FAT identity proof, while retaining stronger scroll/effect checks. A new regression accepts a small digit change and rejects identical species frames. Production source is unchanged by this test correction; the current PR records fresh CI outcomes.
