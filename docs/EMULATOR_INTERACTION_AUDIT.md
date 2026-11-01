# Emulator Sunday integration — fail-closed DeSmuME input verification

This source-only milestone addresses issue #122. C147/PR #124 is already merged on `main`; C146/PR #123 was merged previously. This is **not** a private Nintendo asset build.

## Source of truth

The installed DeSmuME CLI package runs the SDL frontend. Its source keyboard map is `x=A`, `z=B`, arrow keys=D-Pad, unlike the older published Debian manpage that reverses A/B. The workflow logs the actual installed emulator version and SHA-256 of the asset-free development ROM, focuses the SDL window without touchscreen clicks, and holds Right/B long enough to register. No 3DS model, screenshot, original ROM, or private texture is committed.

## Emulator input acceptance

The existing workflow only warned when Right and B produced no meaningful frame changes. The new input gate compares raw XWD frames and **fails CI** unless:
- A visibly opens the Pokédex from HOME.
- Right visibly changes the **lower-screen** Pokédex entry, not just a top-screen clock/animation.
- B visibly returns to HOME, and the resulting frame resembles the prior HOME frame.

Four synthetic XWD regressions cover a successful sequence, ignored Right, ignored B, and corrupt XWD header. This is a visual transition test, not OCR or proof of the exact species number. Actual CI emulator captures must be inspected to confirm Pokémon #001→#002 and B→HOME before closing #122. No test results are claimed before CI completes.

## Sunday parity audit

Original-source animation research C140–C147 has recovered SHA-bound shaders, mesh boundaries, animation track groups, timed vectors, packed quaternion-like keys, source control words and **25,956 source-named transform tracks** across 730 C5 models. It does **not** prove hierarchy, skin weights, clip/action selection, FPS, or native original animation playback. The current native game still uses bounded development geometry previews and partial original-data menu paths. Original textures, shaders, all 36 challenges, DSi AR, sound, and original dual-screen artwork are not fully integrated.

Current public CI can compile an **asset-free** BlocksDS ROM and launch DeSmuME. It cannot prove private original-asset rendering, melonDS or real DS/DSi hardware behavior. These remain release blockers.

## Next gameplay milestone

After the emulator gate passes: once emulator input verification is green, implement source-backed native animation track/clip transport **only where source hierarchy/skin/clip binding is verified**; otherwise prioritize recovering missing source hierarchy, not inventing bone parents or playback. Maintain the strict release parity gate.

## Concurrent merged source milestone

The latest main now includes C148 original C5 skeleton hierarchy recovery (#126): 35,840 original nodes, 31,641 parent links and all 25,956 named animation track/node bindings across 730 models. This is source verification, not native skeletal playback. C149 input verification is rebased on top of C148 without discarding its tests.

## Main branch concurrency

Main advanced through original skeleton C148 (#126) and native original skeleton C149 (#127) while this emulator regression was in review. The emulator gate is intentionally unnumbered, source-only, and rebased on latest main without modifying C148/C149 skeleton tests or gameplay source.
