# C116 — Original 3DS title boot screen + source UV range safety

## Required fidelity

The goal is a port of **every original Pokédex 3D Pro Nintendo 3DS screen and feature**, including **the original 3DS title screen itself**. The title screen must not be redrawn, substituted with the home menu, or excluded. Proprietary source assets remain in the owner's private NitroFS staging, never public GitHub. This code milestone does not establish that the recovered title artwork is already available or matches an original 3DS screenshot.

## Native title boot implementation

The source UI loader now accepts **two separate original title frames**:

- `nitro:/ui/title/t1_title.rgb555`: original 3DS top-screen title image, scaled/converted by the owner for the DS 256×192 display.
- `nitro:/ui/title/t0_title.rgb555`: original 3DS bottom-screen title image, independently recovered rather than copied from the home menu.

Both are **required together**. At startup, after NitroFS initialization, the native DS shows the two original title framebuffers in BG2 of the corresponding hardware screens. A or START or a single touch enters the existing home-menu state **without activating a menu item on that same frame**. If either original frame is missing/corrupt, the development ROM falls back to its explicitly unfinished test menu rather than faking a title. The release asset audit **blocks final release** without two full-size original title frames and still reports that original visual accuracy is **not verified**.

The private packager accepts `title.rgb555`/`title.rgba` (bottom) and `top/title.rgb555`/`top/title.rgba` (top), or the corresponding `bottom/title.*` and `top_title.*` layouts. It writes the two distinct `ui/title` NitroFS files. It refuses an incomplete pair. The existing `HOME` page and 11 original UI page pairs are unaffected. The boot title screen does not claim to reproduce any original 3DS transition timing or animation not yet recovered.

## Native source UV correction

Earlier DS previews converted source `P3UV` normalized signed 4.12 texture coordinates to the DS texture's 12.4 texel coordinates using the selected original texture width/height. However, **negative** or **greater-than-one** original UVs require recovered 3DS wrap/repeat/mirror sampler modes; guessing DS defaults can place Pokémon textures incorrectly.

C116 exposes `previewStreamUvRangeUnit(first,count)` to validate each source triangle/material span. Only ranges with all U/V within inclusive `[0,4096]` are eligible for the existing C115 conservative source-backed color-texture upload. Out-of-unit ranges are **drawn untextured** with the original geometry/face colors; other safe ranges in the same model remain eligible. Invalid boundaries, missing/malformed P3UV and chunked source geometry also fail the texture eligibility check. This does **not** decode original GPU UV transforms or prove that unit-square source coordinates are rendered identically to the 3DS.

## Synthetic tests and remaining work

The C104 native UI regression builds separate private-like synthetic title top/bottom files and verifies distinct pixels and all-or-none loading; the packager tests distinct title assets and rejects a missing original half; the private release audit verifies independent title requirements and refuses missing or malformed assets. The C7 native preview test includes a three-face original-style UV fixture with normalized, negative and >1 source coordinates, verifying per-range gating without hiding geometry. Host tests, BlocksDS ROM compilation and an asset-free DeSmuME smoke test check code paths, **not an original title screenshot**.

Real private original title screens, dynamic transitions, original 3DS GPU texture wrap/filter/UV transformations, accurate original Pokémon animation/materials, source controls and hitboxes, cries/music/voice and full gameplay are **not yet fully ported or validated**. The original title screen remains part of the required final port.
