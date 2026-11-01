# C117 — Private original 3DS title animation timeline playback

The **complete original 3DS Pokédex 3D Pro game**, including its actual title screen, remains the final port target. This milestone adds source-driven native title animation capability; it does **not** invent or verify the original 3DS animation or its duration. No Nintendo artwork or other proprietary data is committed to the public repository.

## Native playback

The separate C116 two-screen original title boot scene still loads private `ui/title/t0_title.rgb555` and `t1_title.rgb555`, and A/START/tap enters HOME without activating an item. C117 optionally reads `nitro:/ui/title/timeline.p3tl`:

- **P3TL v1:** 16-byte header: ASCII `P3TL`, uint16 version 1, uint16 frame count 2–16, uint16 loop 0/1, uint16 reserved zero, CRC-32 of entries; followed by four-byte entries `(index:uint16, vblank_ticks:uint16)`. Index sequence must start at 0 and be contiguous, with each duration in 1–3600 VBlanks. Timing values must come from the owner's **private original 3DS observation/extraction**; the converter does not guess them.
- **Frame zero:** existing independent `t0_title.rgb555` / `t1_title.rgb555` from C116.
- **Frame N, N ≥ 1:** independently recovered `t0_NN_title.rgb555` and `t1_NN_title.rgb555` in `nitro:/ui/title/` using two-digit indices `01` through `15`.
- Playback advances after the declared VBlank duration and holds on the last frame when `loop=false`, or loops back to frame zero when `loop=true`. A missing/tampered later frame stops animation without drawing a half-missing frame over the existing VRAM image; it never fabricates a visual transition.
- Static title behavior from C116 remains available when no P3TL manifest exists. As before, the asset-free development ROM falls back to the development menu if **either original title image is absent**.

The native implementation reuses the two existing 256×192 RGB555 UI page buffers rather than allocating an additional pair. In this milestone a full frame is loaded from NitroFS on a source timing boundary. Original transition effects or audio cues not contained in the recovered images are **not** emulated by guesswork.

## Private packaging

With a verified original frame sequence, the private UI packager accepts `title_timeline.json`:

```json
{
  "loop": false,
  "frames": [{"ticks": 3}, {"ticks": 3}]
}
```

**Illustrative schema only**; the sample durations above are *not* claimed to be from the real game. The owner must supply timing from the actual 3DS source or observations. Additional frames should be independently recovered in `title_frames/bottom/01.rgba` (or `.rgb555`) and `title_frames/top/01.rgba` (or `.rgb555`), continuing for each additional frame. The packager validates both screens for every frame, encodes them to Nintendo DS RGB555 and produces the CRC-protected P3TL. A partial frame pair, invalid JSON schema or unsupported timing fails packaging.

Private final-release auditing checks the optional P3TL header, CRC, ordered frame indices, exact sizes and both title-screen images. It **still** refuses to call the original title visually verified merely because assets or a timeline exist. The static title pair remains independently required by the release gate.

## Regression tests and remaining work

The host-native UI fixture creates a synthetic two-frame title with distinct upper/lower images. It tests different title pixels, deterministic advancement/terminal hold, missing original title art and missing timeline. Python packaging and release-audit fixtures test CRC, frame lengths, incomplete pairs and zero/invalid durations. Native BlocksDS compilation and asset-free DeSmuME boot tests check basic software operation, not a complete original game.

**Still incomplete:** recovery and verified timing of the real original title animation, actual title 3DS-to-DS comparison, sound/music cues, transition compositing effects, original 3DS shader and sampler behavior, all original models and animations, and full application/gameplay parity.
