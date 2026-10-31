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

## Animation inspection controls
In the Pokédex text navigation screen, a validated animation clip enables
touch controls on row 11: tap the left half to pause/resume or the right half
to restart. Restart keeps the current paused/playing state. Selecting another
clip, species or form resets playback and resumes it. SELECT still toggles
original artwork; playback hitboxes are disabled while that artwork is shown.
Missing clips remain static. These controls inspect the existing P3AN transform
transport; they do not implement original skeletal animation.
