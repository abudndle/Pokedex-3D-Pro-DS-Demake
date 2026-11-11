# Development checkpoint - learnset navigation and preview recovery

## Current integration

Branch `codex/c440-learnset-model-recovery` builds on the reviewed #405 gameplay stack and integrates `main` at `9cb9e34f7b90359b68301fcbd90d83e1e2695536`. The C137 test conflict was resolved by retaining both the mapping and texture-validation cases. The earlier checkpoint below describes the prior stack.

- Visible learnset rows with readable Move Dex records now open their exact move. Empty rows and combined touch/button input leave the learnset in place. This is DS navigation over recovered data.
- A malformed legacy DS3M no longer hides a validated P3CS for the same model. The host fixture fails on the old loader and checks all 3,606 emitted vertices after fallback. A genuine melonDS capture shows an authored triangle loading through this route.
- Both private UV staging modes reject pre-existing preview UVs before writing the output archive. The regression caught the previous acceptance and duplicate ZIP member.

Focused learnset, resume, entry, preview and full 730-model synthetic roster host regressions passed. The C136 and merged C137 suites passed 6 and 11 tests respectively. Local `make check-host` stopped at the Windows photo symlink assertion in `tests/c355_photo_viewer.c:47`. The pull request records independent Linux CI and private ROM results.

BlocksDS 1.24 built the authored fixture ROM. In isolated melonDS 0.9.3, the final partial learnset page retained its bottom screen after an empty-row tap, then opened Move 009 for the visible row. Screenshot inspection verified the preview and exact move. The fixture uses no proprietary assets.

The private NitroFS still lacks verified species/form coverage and the source UV, material binding, skinning and animation inputs for full fidelity. Existing milestones #156, #213, #227, #337 and #339 remain open. See issue #301 for the regional Challenge clue gap. Keep original archives, derived assets and private build outputs out of public GitHub and CI.

## Resume point

Current branch: `codex/c404-save-boundary`, stacked on PR #403 (`codex/c403-complete-descriptions`, evidence head `73b781e5eca107be396860b12f51af5543617fd9`), then #401/#400/#399/#397. Main inspected remains `b93ed521f953759e5e538049fa4ce08ad8414d2c`.

Previous verified source: `a683dec76c8067c5d21b288e2f487e41b09c580a`, with all 26 applicable CI workflows passing. Named six-entry Favorites and eight-entry paged Recent history, touch opening, middle removal, empty-row rejection and saved selection/reboot are complete. Private ROM/capture evidence and synthetic FAT/frame evidence are linked in PR #401. Do not repeat completed browser/navigation/Album/Search work.

## New original-text reader

The available original P3DX record holds up to 191 description bytes, but the native entry screen exposed only short excerpts. Description is now a fifth detail tab, accessible through existing START and L/R tab controls. It displays four word-wrapped lines per page with Up/Down and visible previous/next touch controls. Existing source data is used; absent/empty text remains explicitly unavailable. This completes reading of the available P3DX field, not proof that every upstream original string/localization was recovered losslessly.

A bounded reader owns its normalized text, preserves printable source characters, folds console controls into whitespace, clamps page steps and consumes paging touches at boundaries. The original source bytes provide a CRC fingerprint; CRC is integrity/context binding, not source authentication.

Optional P3RV v8 records Description tab/page/source fingerprint, including an unavailable-text view. Source changes or invalid page bindings reset to page zero with a visible notice. Older v1-v7 serialization/decoding retains its prior rules; old v5 still rejects unknown tab values. The former native invalid-tab test now uses tab6 because tab5 is intentionally valid.

Native fail-first regressions cover missing description paging and old checkpoint rejection; pager, strict v8 corruption/torn-slot/cross-process tests and legacy resume tests pass. Independent review identified missing sanitizer flag forwarding in two new runners, which was corrected before publication. Final Linux sanitizer, native ROM and actual emulator outcomes are recorded in this branch's PR; missing/failing checks block readiness.

The public synthetic emulator acceptance uses an authored 191-character/three-page fixture, a short description and an unavailable description. It exercises first/middle/last pages, clamping, previous controls, exact reboot, species changes and a changed source with the same number of pages. A pinned old-production baseline must fail that same acceptance for the expected checkpoint reason before the new ROM can pass.

## Verification evidence

Implementation commit: `01e9ba57c59f7cae3322cd94da2abf38b6ebe32f`, PR [#403](https://github.com/abudndle/Pokedex-3D-Pro-DS-Demake/pull/403), stacked on #401. [C403 independent melonDS 1.1 run](https://github.com/abudndle/Pokedex-3D-Pro-DS-Demake/actions/runs/42342745242) passed: the pinned old ROM rejected the same acceptance for its missing Description checkpoint; the new ROM passed eleven actual frame checks and five real FAT assertions across restarts, including changed-source reset. Its synthetic-only artifact expires after three days; logs preserve the command outcomes.

Independent read-only review reran the downloaded eleven-frame gate and visually confirmed pages 1/3-3/3, exact 3/3 reboot, missing text and changed-source notice. Exported FAT files were not downloaded; FAT results are established by the hosted commands/logs. Linux full host/sanitizer suite and native BlocksDS development/smoke builds passed. Final applicable workflow status is recorded in PR #403; any missing/failing check blocks readiness or merge.

The private BlocksDS 1.24 ROM compiled successfully. All 157 production source files byte-match this implementation. Isolated melonDS core0.9.3 rendered the available one-page original Bulbasaur description; paging touches and keypad clamps retained the same 1/1 frame. This is original-text display evidence, not multi-page original text, full-texture, hardware or DSi camera evidence. Private originals and captures remain outside the public checkout.

## Completed implementation retained

C404 fixes a separately reproduced save-boundary defect: favorite ID 65536 was narrowed to species zero before validation, and capture reported success. Capture now validates signed native favorite IDs 0-648 before conversion and publishes a local candidate only after full validation. Rejected IDs, duplicate favorites or invalid counters leave the destination unchanged. Existing legacy resource-ID filtering on restore and save formats are preserved. The new regression failed on original code, then passed after the production fix; ordinary bridge, cross-process save/torn-slot and deep-resume runners pass locally. Independent read-only source review found no issues. Final hosted checks and private ROM outcome are recorded in the C404 PR; do not infer them from local host success.

- Optional paginated source learnsets, exact detail resume and evolution links.
- Album PNG viewing, exact photo resume, slideshow playback and distinct visible touch bands.
- Bounded model zoom/reset and Move Dex viewport/field reset on explicit bookmark reopen.
- Atomic Recent/Favorite/bookmark handoffs preserving favorites and consuming initiating input.
- Named saved-entry browsers, partial Recent-page bounds and restart continuity.
- Shared Challenge/playback rows, safe footers, Search alignment and clean query redraw.

## Original-source and hardware limits

All 730 native preview structures pass the compiled loader/GL-emission probe, but complete original textured rendering is not verified. Only one species mapping slot is corroborated; original identity/release readiness remains false.

Complete species/form mapping, missing Japanese/English loader tables, original UV/material face bindings, skin weights, mesh-node/action semantics, remaining original Challenge modes, audio and full original GUI remain absent or unresolved. Available direct raw C5 resources in the checked tree are GUI sources. DSi camera/AR and hardware behavior require real devices. Authored synthetic fixtures never establish original-game fidelity.

The asset repository is confirmed private. Original assets, converted outputs, maps, hashes, ROMs and original-asset captures stay in authorized private storage. Public source/CI/artifacts use code and authored fixtures only.

## Next tasks

1. Read the current branch PR and PR #403 for exact source, independent review, all applicable CI and genuine private/synthetic emulator evidence; integrate only under repository check/approval rules. No merge has been performed. A superseded C403 source-head C260 run was cancelled by the checkpoint update; the replacement exact-head workflow must pass before readiness.
2. Reuse #337 original species data, #339 learnsets, #156/#213 geometry and #227 emulator/hardware acceptance. No duplicate milestone was created; leave them open until actual acceptance is met.
3. Recover authorized missing original inputs before claiming full model/material/skeletal/audio/UI parity. Advance independent gameplay/save gaps while blocked, with fail-first and real emulator evidence.
4. Preserve all readable description characters, old save formats, source-change reset, missing-text honesty, original-art gating and model/animation/navigation controls in follow-up work.

No original asset was replaced, no milestone closed, and full-game/hardware completion is not claimed.
