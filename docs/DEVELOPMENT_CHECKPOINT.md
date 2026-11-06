# Development checkpoint - 2026-11-06

## Resume point

Current branch: `codex/c402-saved-entry-browser`, stacked on ready PR #400 (`codex/c401-entry-navigation`), then #399 and #397. Main inspected remains `b93ed521f953759e5e538049fa4ce08ad8414d2c`.

Previous verified source is `0c408a5e410773e57b4f87912710cbee48f996a1`: all 25 applicable CI workflows passed. Seven real melonDS FAT/restart phases and eleven-frame acceptance prove Favorite/Recent entry handoffs, unchanged favorites and same-move bookmark reset. Private ROM production files match that source. Those navigation fixes and prior Challenge/Album/playback/Search work are complete; do not repeat them.

## New saved-entry browser work

Favorites previously displayed only a count and one numeric identifier; both Favorites and Recent list taps were ignored. Actual baseline ROM before/after captures reproduce the inert gestures.

Favorites now shows all six saved entries with recovered P3DX names when available and an honest numeric fallback otherwise. Up/Down and Left/Right select entries; a visible row tap opens it through the verified atomic entry controller. Footer controls no longer overwrite list rows. Empty/invalid/hidden targets are rejected, and simultaneous A plus touch cannot remove an entry.

Recent history now displays recovered names across its two five-row pages (eight retained entries total). Row taps map to the correct absolute page index and open base-form entries without changing favorites. The Recent cursor resets to the opened entry's new MRU position. Stale history cursors are bounded before indexing.

Native fail-first tests cover missing list gestures and the previous footer overlap. Saved-list bounds, page, identity, hidden-control and immutability tests pass, alongside prior entry/navigation/source checks. A dedicated public synthetic melonDS workflow verifies six named favorites, both Recent pages, touch-to-open, middle removal, inert empty-row taps, native FAT identities and restart continuity. Final source-bound build, CI, screenshots and independent review are recorded in the current branch PR; consult it before repeating completed verification.

## Completed implementation carried forward

- Optional paginated source learnsets, exact detail resume and evolution navigation.
- Album PNG viewing, exact photo resume, slideshow controls and separate visible touch bands.
- Bounded model zoom/reset; Move Dex text-window reset on stepping and explicit bookmark reopen.
- Runtime preview-map readiness separate from structural validity and identity verification.
- Readable Records/Types/Move Dex/form/bookmark controls, aligned Search input and clean short queries.
- Shared Challenge/playback control rows, footer safety and original-art gating.
- Atomic Recent/Favorite/bookmark handoffs that consume initiating buttons and preserve favorite data.

## Original-source and hardware limits

All 730 native preview structures pass the compiled loader/GL-emission probe. This does not prove all original textured models render. Only one species mapping slot is corroborated; identity and original-release readiness remain false.

Complete mapping, missing Japanese/English loader tables, original UV/material face bindings, skin weights, mesh-node/action semantics, remaining original Challenge modes, audio and full original GUI remain absent or unresolved. DSi camera/AR and hardware behavior require real devices. Authored synthetic names/animation fixtures are test data, not recovered game content.

Original assets, converted outputs, maps, hashes, manifests, ROMs and original-asset screenshots stay outside public source/CI/artifacts. The repository named `-private` reports public visibility; never run proprietary payload CI there.

## Next tasks

1. Read the new branch PR for exact final source, applicable CI and actual emulator/FAT results. Integrate the stack only under repository check/approval rules. No merge has been performed.
2. Reuse #339 learnsets, #337 original data, #156/#213 geometry and #227 emulator/hardware acceptance; leave them open until actual acceptance is met. No duplicate milestones were created.
3. Recover authorized original inputs before claiming model/material/animation parity. Advance independent gameplay/save defects while blocked, with failing regressions and real emulator evidence.
4. Preserve source-name fallbacks, original-art touch gating, partial Recent-page bounds and unchanged favorite data when extending saved-entry browsing.

No original assets were replaced, no milestone closed, and full-game/hardware parity is not claimed.
