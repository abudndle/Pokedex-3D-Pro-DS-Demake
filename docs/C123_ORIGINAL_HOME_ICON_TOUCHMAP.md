# C123 — Original 3DS HOME icon touch positions, validated against private source

## Requirement and current status

The final Nintendo DS/DSi port should use the **original Pokédex 3D Pro seven-feature HOME icons** (Pokédex, Move Dex, Pokémon Challenge, Records, Album, AR Viewer and Settings), their original layout, animations and the original title screen. Previously, the native DS ROM always used **text development menu row coordinates** for touch controls, even when a recovered original 3DS HOME image replaced that debug menu. That could open the wrong feature when the player touched its original icon.

C123 adds a private **source-measured icon geometry file** that is used only when the actual original bottom-screen HOME artwork is loaded. This is a functional safety/integration milestone, **not** evidence that the original 3DS image/hotspot coordinates have been recovered or visually verified. Do not guess or redistribute any Nintendo art.

## Binary P3HM v1 format and native behavior

Private NitroFS file: `nitro:/ui/home_hotspots.p3hm`. The exact **86-byte** file consists of a 16-byte little-endian header `<4sHHII>`: magic `P3HM`, version 1, seven icons, reserved zero, CRC32 of 70 payload bytes. There are exactly seven ten-byte `<5H>` icon entries: original native destination `P3DPage`, and half-open screen coordinates `x0,y0,x1,y1`, in 256×192 DS bottom-screen touch coordinates. Each rectangle must be at least 8×8, entirely on screen and **not overlap** another icon, and the set of source page IDs must equal exactly `{1,3,6,10,8,9,7}`, with no duplicates, missing, or unsupported features.

On a source-original HOME image, native code resolves touch events **only** through validated private P3HM rectangles, and maps their page ID back to the seven-feature menu. An unavailable map does **not** switch back to development text row coordinates over the source art. D-pad and A remain usable so the user is not locked out if the private source map is absent or malformed. The AR Viewer remains shown but non-enterable when the actual DSi camera backend isn't supported. On the text-only development HOME screen, the existing text-list touch mapping remains enabled; no development positions are asserted to be original-game geometry.

## Owner-private source packaging

In the folder supplied to `tools/package_private_ui.py`, alongside the privately recovered `home.rgba` or `home.rgb555`, optionally supply `home_hotspots.json` with rectangles **independently measured from the actual 3DS source screens**. The format is:

```json
{
  "icons": [
    {"page":"pokedex", "box":[8,8,65,43]},
    {"page":"move_dex", "box":[75,8,132,43]},
    {"page":"challenge", "box":[142,8,199,43]},
    {"page":"records", "box":[8,60,65,95]},
    {"page":"album", "box":[75,60,132,95]},
    {"page":"ar_viewer", "box":[142,60,199,95]},
    {"page":"settings", "box":[8,112,65,147]}
  ]
}
```

**These coordinates are purely synthetic fixture examples**, not verified Nintendo 3DS icon positions, and must never be used for a release or claimed as authentic. The packager requires a real original HOME image when a source map is specified, checks all seven independently supplied page entries, coordinate bounds and nonoverlap, and emits `nitrofs/ui/home_hotspots.p3hm` with a CRC.

The private release audit **requires** a correctly formed and independently measured seven-icon P3HM file for any release, alongside the existing original title/dual-screen art, source models, materials, animation and audio requirements. A matching file alone is not source provenance proof. Private original UI and ROM assets are not committed to the public repository.

## Test evidence and remaining scope

`tests/run_c123_home_hotspots.sh` compiles the native P3HM loader and tests all seven hitboxes, boundary pixels and outside touches, CRC failure, truncation/trailing bytes, unknown or duplicated page IDs, overlapping/outside/tiny rectangles and clearing prior touch maps on failure. Python private packager and release-gate tests exercise the binary layout, source requirements and fail-closed validation. Source checks, the native BlocksDS ROM build, ROM verification and asset-free DeSmuME startup remain required before merge.

Remaining work includes recovering **authentic original HOME image pixels and touch hitbox evidence**, matching its icon animations, actual original UI visual parity, original subtitle/music, genuine DSi camera-based AR, all original gameplay and the full 3DS-to-DS feature set. This milestone does not claim those features are completed.
