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

## Native name-search milestone

Search retains numeric browsing without private assets. With the user's private
`nitrofs/dex.p3dx` catalog, the page also shows original Pokémon names and a
four-row A–Z touch keyboard. Prefixes are case-insensitive and limited to 12
letters. DEL removes a letter; CLR restores numeric browsing. LEFT/RIGHT cycles
matching entries with wraparound; UP/DOWN clears the prefix and jumps ten numbers.
A opens the selected Pokémon and Y retains favorite toggling. No-match queries
keep the selection and show an explicit message. SELECT exposes the text keyboard
when recovered original artwork is displayed; no speculative artwork hitboxes
are assigned.

The existing P3DX v1 loader reads an 8-byte header (`P3DX`, version byte 1,
reserved byte 0, little-endian species count 649), followed by 649 fixed 256-byte
records: name[32], description[192], height[16], weight[16]. Supply verified
original text locally; synthetic fixtures are used only in tests. No original
catalog is bundled. A missing catalog disables the keyboard and leaves numeric
search available. This milestone does not establish original UI visual parity.
