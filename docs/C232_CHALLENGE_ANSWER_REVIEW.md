# C232 — Challenge answer review and aligned touchscreen

## Native gameplay

Previously, answering an existing Pokémon Challenge question immediately replaced it with a new question (or displayed results), so the player never saw which Pokémon was correct. C232 adds an explicit **REVIEW** state between each of the ten existing questions. The current Pokémon, four choices, submitted answer and correct answer remain available. Both the text and native-console fallback display correct/incorrect feedback, chosen/correct species number and running score.

Press A to advance, or tap the visible **continue** text in the native fallback UI (row 19, y=144–167). On question ten, review comes before final results. Submitting again while reviewing is rejected; a repeated continuation after advancing is rejected. The cumulative correct/attempt totals update **on a valid answer only**, while the challenge high score is saved only when the tenth review is dismissed. Replaying the completed challenge preserves its selected region. B keeps the established navigation and save behavior. A combined A+touch press cannot submit twice or dismiss the newly opened review in the same input frame.

## Touch alignment

The four lower-screen question choices render at one-based console rows **11, 14, 17, 20**. The actual first label begins at y=80, not the former y=88. C232 uses a single bounded choice mapper: x=8–247, row spans y=80–103, 104–127, 128–151 and 152–175. The review action is x=8–247, y=144–167. The footer at y=184–191 is not an answer. All custom hitboxes are disabled when unrecovered original 3DS bitmap UI is visible; no original source artwork coordinates are invented.

## Evidence and outstanding work

A test was added **before** the implementation. It failed against old behavior with the expected assertion: `q.stage==P3D_CHALLENGE_QUESTION && q.question==i` after a valid submission. GitHub source-test run 41395416431 recorded this behavioral regression (exit code 134). That test was then updated to require the new review state and explicit continuation, preserving the missing-behavior detection.

`sh tests/run_challenge_smoke.sh` now runs the original Challenge smoke and C232's synthetic regression over all seven supported modes, correct/incorrect answers, unique questions, repeated submissions, replay, ten-question review-to-results and DS coordinate boundaries. The test uses only synthetic game state and source code. `make check-host`, Port source tests CI, BlocksDS development ROM compilation and DeSmuME startup smoke remain the acceptance gates. Emulator boot/screenshot evidence does **not** prove all touch interactions or original-game look.

This is an improvement to existing baseline Challenge gameplay, **not** a claim that the missing 29 original 3DS Challenge modes, original question art, authentic answer audio, multilingual clues or full source-game parity have been restored. No Nintendo assets or private source metadata are committed.
