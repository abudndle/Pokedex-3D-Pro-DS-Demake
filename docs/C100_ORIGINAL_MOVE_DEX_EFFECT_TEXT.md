# C100 — Restore original Move Dex effect text on Nintendo DS

The original ROM-derived P3DM record loader was already present, but the DS menu only displayed and scrolled `description`. The separately recovered **original `effect` field** was loaded but inaccessible in the game.

## Source-derived completion

- All **559 original move records** are present in the user's private `moves.p3dm`; their recovered names are not procedural replacements.
- Of those records, **548** contain an original description and **359** contain an original effect. **11 description fields and 200 effect fields are empty in the recovered data**. These remain empty; the DS menu never invents text for them.
- In the Move Dex, **X** switches between the original description and original effect. The selector initially shows the description; **L/R** and the existing text-screen touch scroll navigation work in both modes.
- On changing move, the view scroll offset resets to zero. On changing field, the scroll offset resets to zero. Existing Move Dex navigation, controls and save formats remain unchanged.
- New C helper `move_text_view` bounds scrolling to three 28-character lines and never substitutes one field for another.
- Verified locally on Linux with strict C compiler flags and all 559 private records, including the initial `Pound` record, whose recovered effect is distinct from its description.
- Public source-only host regression compiles a synthetic `P3DMove` fixture and checks content selection, scrolling, clamping, null inputs and empty effects.

## Original-game completeness boundary

Showing a recovered original field is a **real source-data game feature**, not proof the entire 3DS Move Dex UI is identical on DS. Exact original 3DS artwork hitboxes, full battle properties, speech/audio, language-localized text and complete gameplay remain unfinished. The 600/1800-triangle native model previews are still low-detail diagnostics, not final original 3DS render fidelity.

C100 also fixes the C99 parity row's source evidence link to `source/preview_stream.c` rather than the standalone audit tool, so the strict `check_feature_parity.py` schema continues to validate. All required features remain incomplete until original end-to-end tests prove parity, and the C85 final-game release gate stays blocked.

Private source text and 3DS assets are **not** checked into public GitHub. The original game extraction stays in the user's own private NitroFS package.
