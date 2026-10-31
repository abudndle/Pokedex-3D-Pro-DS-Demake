# C77: Private source-backed P3PX texture conversion

The user's own previous-chat C7 original texture ZIPs and C75 SHA-256-verified metadata were processed offline. Source conversion confirms exact C7 RGB555/alpha8 lengths and the cross-archive C75 model, texture index, dimensions, original source offset and original raw SHA-256. No original image or model payload is committed here.

## Checkpoint
- 4,039 recovered original texture records inspected across 726 source-model archives.
- 3,251 textures are completely opaque (all alpha8 values 255), RGB555 opaque bit 15 is set for every pixel, and may be packaged directly into P3PX v1 (magic P3PX, version u16, width u16, height u16, RGB555 pixels).
- 788 textures have non-opaque alpha; **none** is silently converted to opaque RGB555.
- 705 of 726 models exceed the current 128 KiB model texture VRAM budget **if all their opaque images are uploaded at once**. Upload only verified material-referenced textures with the existing VRAM guard. This is not proof that 705 models cannot work.
- Private ZIP names now use `textures/pNNN/tIII.p3px`, preventing cross-model filename collisions. The native viewer selects `nitro:/textures/pNNN` for each resource.
- All conversion and integrity checks passed locally, including ZIP CRC, with five synthetic Python tests. Native smoke CI and emulator visual validation are separate.

## Gating and limitations
Existing `P3MT` model/material maps and `P3TX` DS size/texture manifests must be created from verified original assignments; this milestone **does not** fabricate them. The C7 source converter's original channel interpretation, alpha behavior, source UV orientation and material bindings are not claimed completely faithful. P3PX images remain private. The source-only ZIP conversion tooling can be run on private inputs; no original payload or PNG belongs in GitHub.

## Next milestone
Decode and verify original mesh/material bindings by model family, resolve translucent source formats with correct DS transparency semantics, then test actual Pokémon skins in melonDS and on hardware.
