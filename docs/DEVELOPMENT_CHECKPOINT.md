# Development checkpoint - complete descriptions

## Resume point

Current branch: `codex/c403-complete-descriptions`, stacked on ready PR #401 (`codex/c402-saved-entry-browser`), then #400/#399/#397. Main inspected remains `b93ed521f953759e5e538049fa4ce08ad8414d2c`.

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

1. Read the current branch PR for exact source, independent review, all applicable CI and genuine private/synthetic emulator evidence; integrate only under repository check/approval rules. No merge has been performed.
2. Reuse #337 original species data, #339 learnsets, #156/#213 geometry and #227 emulator/hardware acceptance. No duplicate milestone was created; leave them open until actual acceptance is met.
3. Recover authorized missing original inputs before claiming full model/material/skeletal/audio/UI parity. Advance independent gameplay/save gaps while blocked, with fail-first and real emulator evidence.
4. Preserve all readable description characters, old save formats, source-change reset, missing-text honesty, original-art gating and model/animation/navigation controls in follow-up work.

No original asset was replaced, no milestone closed, and full-game/hardware completion is not claimed.
