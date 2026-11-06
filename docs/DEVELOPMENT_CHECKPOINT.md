# Development checkpoint - 2026-11-06

## Resume point

Current implementation branch: `codex/c400-gameplay-touch-flows`, stacked on verified PR #397 (`codex/c361-runtime-model-map-gate`). Main inspected remains `b93ed521f953759e5e538049fa4ce08ad8414d2c`.

Previous fully verified source is `cf530d975f4f7dfc2aede4052bd0606efd69d060`: all 25 applicable independent PR workflows passed, plus BlocksDS 1.24 private ROM rebuild and genuine isolated DeSmuME and melonDS 0.9.3 captures. PR #397 is ready and unmerged. Search alignment and short-query redraw are complete: do not repeat them.

## Completed implementation carried forward

- Paginated optional source learnsets, exact detail-page resume and evolution navigation.
- Album PNG viewing, exact open-photo resume, slideshow play/pause.
- Bounded native model zoom/reset, Move Dex text-window reset on move navigation.
- Runtime preview-map readiness separated from structural validity and identity verification.
- Readable Records/Types/Move Dex/form/bookmark controls and zero-based Search targets.

## New gameplay interaction slice

- Challenge choices use their actual zero-based row positions; padded choice cells no longer select the next answer. Fourth choice stops before the Back footer. Review Continue uses its visible band. Renderer and touch code share row constants.
- Album filename selection, photo opening, page navigation, slideshow controls and return-to-list use separate visible bands. Filename taps cannot become page actions, and invalid/hidden/empty selections cannot open a photo. The destructive delete flow still requires its explicit confirmation.
- Optional validated P3AN playback pause/restart now uses visible row 12, preserving unavailable/static-source/original-art gates. This is not original skeletal animation restoration.

Fail-first native regressions reproduced all three original defects, then passed after production changes. Related Challenge, source-backed continuation, Search, Album viewer/slideshow and source smoke checks are preserved. New Album touch tests are in canonical host CI, including Linux sanitizers. The real melonDS FAT Album replay uses interior coordinates matching the controls. Final source-bound ROM/CI results and captures are recorded in the branch PR; check those before repeating completed verification. Missing or failing checks block merge.

## Private assets and genuine limits

All 730 native preview structures pass the compiled loader and exact GL-emission probe; this does not prove all 730 original textured models render correctly. Runtime species mapping has only one corroborated slot. Identity and original-release readiness remain false.

Private original assets, converted outputs, manifests, hashes, ROMs and captures remain outside public source, CI and artifacts. The repository named `-private` reports public visibility; do not run proprietary payload CI there.

Complete canonical species/form mapping, missing Japanese/English original loader tables, original UV/material face bindings, skin weights, mesh-node/action semantics, remaining original Challenge modes, original audio and full GUI behavior remain absent or unresolved. DSi camera/AR and hardware-specific behavior require real hardware evidence. Preserve DS fallback gating.

## Next work

1. Read the current branch PR for exact final source, independent review, all applicable CI and private emulator acceptance. Integrate only under repository merge/check/approval rules; neither existing PR #397 nor this slice is a full-game release.
2. Reuse #339 learnset acceptance and #337 original species data; keep #156/#213 geometry and #227 emulator/hardware acceptance open until their actual criteria are met. No duplicate milestone was created.
3. Recover authorized missing original inputs before claiming model/material/animation parity. Continue independent gameplay/save improvements while those inputs are blocked.
4. Optional P3AN UI has host verification; original clip/whole-game animation and hardware parity remain unverified. Public synthetic Album/Challenge emulator tests do not prove original camera/photo fidelity.

No milestone has been closed or merged, and full-game completion is not claimed.
