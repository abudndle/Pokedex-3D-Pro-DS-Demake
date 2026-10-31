# DS-Homebrew implementation references

This project uses DS-Homebrew projects as **technical references**, not sources of proprietary Pokémon content.

## References and what to reuse

- [TWiLight Menu++](https://github.com/DS-Homebrew/TWiLightMenu): dual-screen Nintendo DS/DSi menus, SD-card browser and launcher structure, themes, and lightweight image viewing. Its README documents `make package` at the repository root and `make dist` in component directories; those targets are not BlocksDS build commands. Its `imageview`, `romsel_dsimenutheme`, and `settings` subprojects are useful references for the Pokédex's photo album, UI assets and settings.
- [nds-bootstrap](https://github.com/DS-Homebrew/nds-bootstrap): launch behavior, SD-card paths, save-file expectations and compatibility when running a homebrew `.nds` on DS/DSi/3DS via TWiLight Menu++. Its README documents `.sav` for DS ROM saves and `.pub`/`.prv` for DSiWare; those are launcher conventions, not a promise that this project's custom FAT save path automatically works. Use it for runtime interoperability, **not** as a graphics or 3D model source.
- [GodMode9i](https://github.com/DS-Homebrew/GodMode9i): read-only file-browser conventions and DSi/SD-card storage handling. Keep file operations carefully bounded, especially imported assets and save data.

## Port-specific implementation rules

1. Keep the **asset-free** BlocksDS build usable on a standard DS without DSi-only features. Check hardware capability before exposing DSi camera and SD-only operations.
2. Read immutable packaged data through NitroFS; use writable FAT storage only after initialization succeeds, and never present an unconfirmed write as a successful save.
3. Adapt image-viewer techniques to 256×192 screen constraints and DS video-memory limits. Convert source assets offline to compatible palettes/bitmaps instead of attempting to decode 3DS formats at runtime.
4. Keep original Pokémon assets outside the public repository. Import locally from the user's lawful copy during a dedicated asset stage; no assets or full source trees from DS-Homebrew should be copied in unless their license and attribution requirements are satisfied.
5. For actual hardware verification, test plain DS startup and controls, TWiLight Menu++ / nds-bootstrap launching, returning from pages with B, NitroFS reading, optional FAT saves, and 3D previews where data exists.
6. Compare the DS-mode rendering against the original source UI *only after* the source asset extraction yields verified filenames and dimensions. A generic debug menu does not establish visual parity.

## Build-environment note

TWiLight Menu++ documents devkitARM, libnds, grit and mmutil via devkitPro, and nds-bootstrap documents devkitARM plus Nintendo DS libraries, while this repository uses **BlocksDS** for its native smoke build. These are alternate toolchains; do **not** mix incompatible build flags or libraries simply because the code targets Nintendo DS.

## Current limitation

These references do not themselves fix GitHub Actions runner failures. Recent source/port/native jobs returned failures with empty step lists and inaccessible job logs; diagnose Actions permissions, usage/billing, and runner startup independently of game logic.
