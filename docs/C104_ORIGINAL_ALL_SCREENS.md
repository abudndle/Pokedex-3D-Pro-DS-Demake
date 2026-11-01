# C104 — Original 3DS appearance remains the target for every page

The intended deliverable is a faithful port of **Pokédex 3D Pro** to Nintendo DS/DSi, not a new design, a reference mock-up, or a home-menu-only port. Keep the recovered original layout, art, Pokémon models, animations, UI behavior, data, and audio wherever technically possible on target hardware. Original game files remain private and are not stored in GitHub. Hardware differences must be documented rather than replaced with purportedly original assets.

## Native UI fix

The original-art loader previously handled 10 destinations (Home through AR), but silently rejected **Records**, despite the feature menu containing an eleventh page. C104:

- Adds P3D_PAGE_RECORDS (index 10) to the native original-art loader, using the shared page enum.
- Supports private nitro:/ui/pages/t0_10_records.rgb555 along with existing page images.
- Updates the private packaging tool to stage records.rgb555 or records.rgba.
- Requires Records artwork in the private original-art release inventory.
- Adds a C host-side loader test using synthetic bitmap files and a simulated DS screen, plus packaging and release-gate regressions.

## Scope and limitations

This fixes page coverage in the **existing bottom-screen 256×192 original-art loader**; it does **not** mean the original 3DS interface is fully reconstructed on either screen. Original touch hitboxes, animations, 3DS-to-DS screen transforms, top-screen visuals, material/shader associations and private emulator comparisons remain incomplete. The text-mode UI is a development fallback, not the required final appearance.

Test without Nintendo assets with: sh tests/run_c104_original_ui_pages.sh and python3 tests/test_private_ui_packager.py. Public CI uses synthetic fixtures.
