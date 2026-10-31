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

## Native name-prefix search
The Search screen now uses the existing seekable P3DX private text catalog for
name-prefix matching, controller/text-screen input and previous/next results.
Numeric search remains available without original text. See
[Native Pokémon name search](NAME_SEARCH.md) for controls and catalog format.
