# Native development ROM

The GitHub Actions **Native BlocksDS development ROM** job produces a boot-format `.nds` artifact in a BlocksDS container.

**This is a developer smoke ROM, not a completed demake.** It has a minimal text-based test menu, not the original 3DS user interface or finished Pokémon renderer. The original C14 main game loop and accurate original assets still need to be migrated and integrated.

## What CI verifies
- The ARM9 program compiles and links using the actual BlocksDS toolchain.
- `ndstool` produces a nonempty ROM with ARM9 and ARM7 sections.
- Host regressions test Dex, Move Dex, challenge, saves, album, custom backgrounds and associated UI state.

## What CI does not verify
- Booting or graphical correctness in melonDS.
- Every original Pokémon, appearance, materials, animations or data tables.
- Nintendo DSi enhanced mode and camera AR.
- Complete native gameplay.

The private original game assets must not be committed to GitHub. Final game ROM assembly will be done using the asset integration process with the user's own originals.

## Challenge answer review
Challenge submissions now hold the current question on a review screen showing
correct/incorrect feedback, the submitted Pokémon number, and the correct number.
Press A or tap the continue label to advance; the tenth answer is reviewed before
results appear. Each answer updates cumulative progress once, at submission.
Repeated input during review cannot add another answer or score. B retains the
existing return-to-menu/save behavior; replay retains the selected region.

Text-mode answer hitboxes now start at y=80, matching console row 11, and end
before the footer at y=176. Review uses its own continue target at y=144–167.
Touch input remains disabled over original artwork; A continues to work there.
This improves the existing quiz flow; original question clues and asset-integrated
challenge presentation remain unfinished. No private original assets are needed
for these host regression fixtures.
