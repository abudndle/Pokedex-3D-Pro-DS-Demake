# C106 — Original-source upper HUD composited over live 3D Pokémon

## Required original-game behavior

Every menu, screen, model and feature should faithfully port Pokédex 3D Pro's actual original 3DS appearance to DS/DSi. This milestone adds the missing hardware composition path for the upper Dex screen. It does **not** claim source artwork has been visually authenticated or that the port is finished.

## Native renderer

- The live Pokémon model stays in the main DS 3D engine on BG0.
- The source-derived upper Dex HUD is supplied **separately** as a 256×192 A1RGB555 bitmap and displayed on main BG2 with higher priority.
- Pixels with bit 15 set paint original interface artwork. Pixels with bit 15 clear expose the live 3D Pokémon beneath them.
- The existing full-screen upper artwork remains for non-model menu/info pages; the lower original touch artwork remains independent.
- A 3D view only loads its overlay if the original mask exists and contains both opaque UI pixels and transparent model pixels. Missing/short/all-opaque/all-transparent masks are rejected. When unavailable, the native Pokémon model still renders with no fake HUD.
- The dev SELECT toggle disables source art for both screens; changing screens restores the appropriate bitmap/overlay or text fallback.

## Private source asset format

Stage an original, source-verified cutout in **top/dex_overlay.rgba** or **top/dex_overlay.rgb555** inside the private UI source directory used by tools/package_private_ui.py. It is exported to **nitro:/ui/pages/t1_01_dex_overlay.rgb555**. The source RGBA alpha channel is binary-mapped to DS A1RGB555 (transparent alpha 0, visible nonzero alpha). The cutout must come from the actual recovered 3DS interface; never generate it by guessing HUD coordinates, nor copy the opaque background over it.

The final private original-assets audit requires an original-derived Dex overlay independently of the 22 full-screen page art files. Copyrighted source assets remain private and are not committed to GitHub.

## Synthetic verification and remaining limits

The C host fixture checks separate top/bottom framebuffers, bit15 transparency preservation, invalid masks, and harmless no-draw on failure. Packaging tests convert synthetic RGBA masks and reject opaque fakes; release audit tests missing and malformed masks. Public CI's asset-free ARM9 ROM and DeSmuME startup checks are **not** a verified source-assets visual comparison.

Still missing: actual recovered correct source HUD mask, exact 3DS model placement and compositing fidelity, fully verified original textures/materials, animations, sounds and gameplay, original hitboxes/transitions/localizations, and private asset-enabled melonDS and device testing.
