# C336 — DSi camera / QR integration: verified upstream mapping and safety contract

This is an **integration plan**, not a claim that AR camera capture, QR recognition, wireless import, or original 3DS AR rendering has been implemented. It complements C335 Nitro Engine/DSMA, which handles source-derived 3D geometry, not the DSi camera sensor.

## Upstream references and actual scope

| Reference | Useful subsystem | Integration restriction |
| --- | --- | --- |
| [Epicpkmn11/dsi-camera](https://github.com/Epicpkmn11/dsi-camera) | Minimal DSi dual-camera ARM7/ARM9 initialization, capture, and IPC example | Separate devkitARM/libnds application: port interfaces to BlocksDS/calico-compatible ARM7/ARM9 code and verify hardware. No blind drop-in. |
| [addisonking/dsi-camera](https://github.com/addisonking/dsi-camera) | Expanded capture, gallery, SD export and media handling; fork of Pk11 | DSi-native; test buffer ownership, formats, capture latency, memory, and platform dependencies before reusing. |
| [Epicpkmn11/dsidl](https://github.com/Epicpkmn11/dsidl) | DSi camera QR decoding, scan guide/overlay, optional network download UX | It scans URL/script QR codes. This does **not** implement 3DS Pokédex AR-marker semantics or establish safe automatic execution/download. Never run downloaded scripts from QR payloads. GPL-3.0 project: check licensing before copying code. |
| [devkitPro libnds API](https://libnds.devkitpro.org/) | Hardware API reference for older devkitPro examples | Port to this repository's **BlocksDS** libnds and ARM7 infrastructure rather than mixing devkitPro libraries/binaries. |
| [BlocksDS core libraries](https://blocksds.skylyrac.net/docs/libs/core_libs/) | Actual toolchain, libnds, calico, filesystem / core API | Use BlocksDS-provided headers and versions as compilation authority. |

Upstream examples are **technical references**. Do not copy their source wholesale or assume their device initialization is safe in the existing game context. Review each upstream license and preserve attribution where required.

## Current repository integration points

- `source/dsi_features.c` and `.h`: `p3dCapabilities(dsi_mode,sd_ready,camera_ready)` provides hardware feature gates. Existing AR item is *visible but disabled* when unavailable. Do not set `camera_ready` based solely on DSi model detection.
- `source/main.c`: preserves Pokédex screen, input and save lifecycle; avoid resetting VRAM, existing GL preview or interrupt ownership when entering/exiting AR.
- `source/photo_album.c`: independent storage/display concerns. Treat AR session screenshots as optional user content only when filesystem initialization succeeds.
- `source/nitro_source_bridge.c` (C335 branch/PR): top-screen 3D source geometry. The camera feed and AR projection need separate hardware-tested integration. Nitro Engine initialization is not DSi camera initialization.

## Implementation sequence (bounded milestones)

1. **Sensor backend, DSi-only.** Audit ARM7 I2C/Aptina setup, ARM9 frame pipeline, PXI/IPC ownership and calico interactions. Introduce a backend interface with explicit states `UNAVAILABLE`, `CLOSED`, `OPEN`, `STREAMING`, `ERROR`. Opening requires successful DSi-capability and hardware initialization. Failed open clears readiness and leaves the AR button disabled.
2. **Buffer and lifecycle safety.** Bound frame size, stride, pixel format, allocation, and capture rate before conversion to the DS 256x192 viewport. Verify camera switch, foreground/back transitions, shutdown, restore of video/IRQ state and power-down. No camera access on DS or DS Lite.
3. **User-facing AR flow.** Enter camera preview only on verified DSi. Preserve existing title/entry page, touch input and original Pokémon render path. Validate camera permission/access in actual DSi mode (emulator support is not proof of physical hardware).
4. **Source-verified AR marker handling.** Discover the original Pokédex 3D Pro marker format, mapping, orientation and transforms from authorized original data. QR URL scanning in dsidl is an independent example, *not* proof of compatibility with Nintendo AR cards. Unknown/corrupt marker payloads fail closed.
5. **Optional scan / album / SD.** Only after a supported format and bounded decoder are verified. Restrict QR to explicitly supported data; never execute scripts, open arbitrary download URLs automatically, or silently write files. Respect existing save/resume semantics.
6. **Test matrix and evidence.** Host tests for zero/false capability states, short buffers, bad dimensions, frame-drop recovery, repeated init/shutdown, invalid payloads and save resume; asset-free BlocksDS ARM9+ARM7 ROM, real melonDS DS-mode no-camera path, DSi-mode camera capability smoke, and physical DSi hardware tests. Preserve screenshots/logs without personal camera imagery or proprietary assets.

## Explicit release gates

- **DS / DS Lite:** original Pokédex, Move Dex, Challenge and saves still work; AR remains disabled.
- **DSi with failed sensor init:** never enter AR; show unavailable state; no bogus camera-ready flag.
- **DSi with working sensor:** only verified camera frames can be rendered; safe shutdown and recovery.
- **Original 3DS AR fidelity:** remains *unverified* until genuine marker mapping, original geometry/materials/animations and visual comparisons are completed.
- Keep commercial Nintendo assets, personal photographs, camera frames, decrypted archives and private conversion outputs out of public GitHub, CI logs and artifacts.

## Relationship to C335

C335 uses Nitro Engine + DSMA to consume converted original 3D model data. C336 concerns actual DSi-only camera acquisition and original AR semantics. Keep builds separate until both boundaries have proven hardware-safe tests; do **not** combine a speculative camera driver with an in-progress rendering merge.
