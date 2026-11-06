# Development checkpoint - 2026-11-05

## Resume point

Integrated branch: `codex/c361-runtime-model-map-gate`, PR #397 against main.
Main inspected: `b93ed521f953759e5e538049fa4ce08ad8414d2c`.
Last fully verified source before this checkpoint: `da237e00c7f92ed71f9bf2a480c91c316b43f153`.
All 25 applicable PR workflows passed for that source, including Linux host/sanitizer tests, BlocksDS, synthetic native zoom, melonDS FAT save/resume, evolution, Move Dex and Album checks. No merge has been performed.

## Implemented slices in the integration

- Paginated optional source learnsets, exact detail-page resume and evolution navigation.
- Record Album PNG viewing, exact open-photo resume, slideshow play/pause.
- Native model zoom/reset with bounded distance and visible-label touch bounds.
- Move Dex navigation resets the text window when changing moves.
- Runtime preview-map readiness separated from structural package validity and identity verification.
- Zero-based DS console layout: seven Records scores fit, data and controls remain readable, and Back hints use free rows.

These are bounded implementation slices, not verification of the complete original game.

## Local private verification

BlocksDS 1.24 rebuilt the integrated private-asset ROM. All 149 staged source files matched the verified source. An isolated DeSmuME libretro process booted that ROM and captured genuine framebuffers for menus, native model zoom/reset, Records, Types and Move Dex. Model reset was pixel-exact; near/far changed visible model size. Public CI uses synthetic assets only. Original payloads, ROMs, maps, hashes, manifests and screenshots are outside this public repository.

All 730 native preview structures pass the compiled loader and exact GL-emission probe. This does not prove all 730 original textured models render correctly. Runtime species mapping currently has only one corroborated slot. Original identity and release readiness remain false.

## Open source/hardware blockers

- Complete canonical species/form mapping is not verified; do not infer it from model file order.
- Available recovery lacks the Japanese and English original loader tables needed for the full identity/data join.
- Original UV/material face bindings, skin weights, mesh-node/action semantics and full skeletal playback remain absent or unresolved in the staged pack.
- Remaining original Challenge modes, original audio and full source GUI behavior remain unfinished.
- DSi camera/AR and device-dependent features require actual hardware evidence. DS fallback gating must remain.
- The asset repository named `-private` currently reports public visibility. Do not put proprietary outputs into its CI or public artifacts.

## Next work

1. Search touch bands now use zero-based rows, preserving original-art gating and all 26 letters/actions. The native regression fails on previous production code at the lower N touch-cell boundary; updated native Search and query tests pass. Refresh ROM captures and CI for this follow-up before treating it as verified.
2. Refresh the source-bound tests/build/emulator evidence after any production change, then independently review PR #397. Missing or failing checks block merge.
3. Reuse open #339 for learnset acceptance and #337 for genuine original species data; keep #156/#213 original geometry and #227 emulator/hardware acceptance open until their actual criteria are met. Do not create duplicate milestones.
4. Recover authorized missing source inputs before claiming complete model/material/animation or game parity. Continue independent gameplay improvements while those inputs are blocked.

No milestone has been closed and no full-game completion or hardware verification is claimed.
