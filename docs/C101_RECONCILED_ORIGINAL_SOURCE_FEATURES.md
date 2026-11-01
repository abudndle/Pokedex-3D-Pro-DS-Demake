# C101 — Integrate high-detail source models with original Move Dex effects

C101 resolves a pending feature-integration gap. The C98 geometry detail selector was on an older unmerged branch, while C100 had already merged the actual recovered original Move Dex descriptions/effects. C101 combines both into the current native source without deleting either feature.

## Implemented together

- Original P3DM **559 move names**, 548 recovered descriptions, and 359 recovered effects: select description/effect with **X on the Move Dex page**, scroll with L/R. Missing original fields remain missing.
- Original-derived DS3M legacy geometry remains default; **X on Settings** opts into CRC-validated P3CS source geometry when privately staged (up to 1,800 triangles in 600-triangle streaming buffers), and another X switches back.
- Missing or malformed high-detail chunks fail closed or safely fall back to a valid legacy file. No unverified color or normal-map texture binding is activated by this mode.
- The detail selector is a **development/test setting**, not an invented original 3DS preference, and it is not saved to original-game save data.
- Public synthetic tests include actual C renderer frame/triangle counts, a corrupted P3CS fallback, the C98 private-packager schema, and source-only C100 Move Dex field selection and scrolling.

## Private original-source evidence

The user's private C98 NitroFS package contains 726 original-derived legacy previews and 500 original-derived chunked model previews; all 500 chunk payloads and IDs have passed private CRC/source inventory validation. Original source move corpus contains 559 records. All copyright-protected original-derived content stays outside the public source repository.

## Not completion of the 3DS game

The port still needs original-GPU sampler and shader behavior, complete source Pokémon animations/models and effects, original artwork hitbox mapping, many missing challenge modes, soundtrack/cry audio, complete localizations and DS/DSi hardware validation. Private original-data melonDS screenshots have not been captured; GitHub's source-only DeSmuME smoke is not equivalent.

The strict C85 release gate remains blocked. An asset-free ROM compile verifies source integration only, not that a model renders like the original 3DS game.
