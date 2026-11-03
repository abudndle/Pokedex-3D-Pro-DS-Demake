# C331 — Original P3DX clue and option binding for text Challenge

## Scope and provenance
Rebases the useful source-backed text-quiz approach from older unmerged PR #42 onto current C232 answer REVIEW and C330 replay-seed semantics. No proprietary assets are committed, copied or synthesized as if original.

The seventh baseline mode, "POKEDEX TEST", remains unlocked at 50 answered questions. Each live question now reads its Pokémon's description and four answer species' names from the optional private `nitro:/data/dex_en.p3dx` catalog. Names and clues are not embedded in the public ROM; a standalone asset-free development ROM displays **Original P3DX clue/options missing** and prevents answers in this mode. The other six baseline regional number modes are unchanged.

## Gameplay
- The top text fallback shows two 28-character description rows, with L/R paging bounded by the loaded description; the lower fallback displays four source species names.
- If the source is missing, corrupt, lacks the required description or any answer name, or the current question/choice invariants are invalid, `p3dChallengeTextAnswer` rejects the submission and does not affect score, attempts or progression.
- Every answer reloads the exact current question from the catalog; stale previously loaded text cannot authorize the next question.
- Correct/incorrect feedback and explicit review-to-next transitions remain current C232 behavior, including question-ten review before results. The same source-backed names are displayed during review when available.
- Fallback text hitboxes are not inferred for original 3DS bitmap artwork; the regular DS/DSi camera restrictions and save formats are unchanged.

## Evidence
1. RED: independent Port source tests on red-stage commit `e351dfbf333cf38316b97e1ba895b78c4f8ce3e1` failed at `tests/test_c331_challenge_text.c:16: p3dChallengeTextLoad(&text,&quiz)`, proving the absent behavior.
2. GREEN: C331 Challenge regression exercises a 649-record synthetic P3DX catalog, ten questions with review, correctness, option names, clue paging, invalid/stale choices, missing catalogs/names/descriptions, and absence of score mutation on failure.
3. Run locally with `sh tests/run_c331_challenge_text.sh`, `sh tests/run_challenge_smoke.sh`, and `make check-host`. Independent GitHub CI executes the focused test from `.github/workflows/port-source-tests.yml`.
4. Native BlocksDS and emulator gates remain distinct from the synthetic-host behavior tests. Evidence for original Nintendo source text, original visual art, authentic other 29 modes and 3DS hardware fidelity is **not** claimed by this work.

## Remaining original-game gaps
Full original 36-mode challenge design, exact answer rules, original question artwork and audio, private verified text/cues, native screenshots compared against original 3DS gameplay, real console acceptance, and completed original Pokémon models/textures/animations.
