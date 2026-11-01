# C105 — Independent original 3DS artwork for both DS screens

## Scope

The final game must preserve the original Pokédex 3D Pro design on **both** screens, for **every** menu and gameplay page. Development consoles and synthetic examples are temporary fallback and test infrastructure, not original artwork.

C104 added the previously missing Records UI destination. C105 now adds source artwork loading on the **upper main DS screen** independently from the existing lower touchscreen. The private asset packaging format contains 11 upper page bitmaps (t1_) and 11 lower page bitmaps (t0_), for 22 screen-specific files. The release asset audit requires both sets.

## Native renderer behavior

- Source-based menu/info pages with a valid private upper bitmap display it on main BG2 in MODE_5_3D. The upper text console is disabled to prevent corrupting the 128 KiB bitmap VRAM bank A.
- Switching to an active Pokémon model preview restores MODE_0_3D, reinitializes the upper text-console fallback and gives native BG0 to the model renderer, without using guessed source texture samplers.
- Switching back to menus restores upper source artwork. SELECT toggles the developer original-art/text fallback for both screens simultaneously.
- Independently recovered top art is loaded from nitro:/ui/pages/t1_<NN>_<name>.rgb555; bottom pages remain t0_. The packager reads upper source files from the private top/ folder (or top_<name>.rgba or .rgb555) and never copies a lower bitmap to replace missing upper art.

## Verification

- The native C host fixture tests upper and lower screen contents independently, including Home, Records, missing files and safe framebuffer behavior.
- The Python private page packager tests independent source conversion and count.
- The release audit now lists a missing upper page as a release blocker.
- GitHub asset-free ARM9 ROM compilation and DeSmuME smoke are evidence of native source compatibility, **not** original 3DS visual parity or a tested original-asset ROM.

## Remaining release blockers

The upper original background is deliberately **not overlaid** on an active 3D Pokémon model: source-verified masking, UI layout and 3D compositing need separate work. Accurate original source artwork, sprites, buttons, touch hitboxes, animations, game sound, full source meshes/materials, localized data, challenges, and private-asset melonDS/hardware comparison remain incomplete. Original proprietary data stays private.
