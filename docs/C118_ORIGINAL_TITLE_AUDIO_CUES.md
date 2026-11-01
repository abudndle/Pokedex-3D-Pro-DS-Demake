# C118 — Source-timed original 3DS title audio cues on Nintendo DS

## Goal

The requested target is **all of the original Pokédex 3D Pro 3DS title, menus, models, transitions, animation, music and gameplay on Nintendo DS/DSi**. This milestone supports **short original title audio cues only**. It does not supply proprietary audio, decode unverified original cues, recreate title music, or assert that the original 3DS title screen and sound now match. Original game assets belong only in the owner's private asset staging.

## Native title audio implementation

The existing C116/C117 original title is unchanged: it uses independently recovered original upper and lower title bitmaps and an optional source-specified private P3TL frame timeline. C118 adds optional **P3TC source-observed cue mapping**, either for a static one-frame title or a P3TL animated sequence. Nothing emits an invented sound if original audio is not provided.

- `nitro:/ui/title/cues.p3tc` — header `<4s4HI`: `P3TC`, version 1, title frame count (1–16), number of cues (1 through frame count), reserved zero and CRC32 of records; records `<HH` hold strictly increasing frame index and cue ID in 1–16. Frame count must match the private P3TL timeline, or equal 1 for the static title.
- `nitro:/ui/title/audio/cNN.p3sa` — header `<4sHHII`: `P3SA`, version 1, source sample rate 8000–32000 Hz, number of signed PCM16 mono samples (1–16384) and CRC32 of the little-endian sample bytes; the exact sample payload follows. This limits each cue to 32 KiB and avoids a large in-memory soundtrack implementation.
- The DS native renderer calls BlocksDS libnds `soundEnable()` / `soundPlaySample(..., SoundFormat_16Bit,...)` only when a valid private original P3TC event exists. A frame-zero cue starts with the title. Subsequent cues play only when the corresponding source frame is shown. The sound buffer remains resident while ARM7 plays it; any old cue channel is killed **before overwriting the PCM buffer**. A/START/touch stops the title cue and enters HOME once. Absent/malformed cue map or PCM means silence, never a substituted commercial or invented jingle.
- No original source transition fade timing, full theme playback or other game sound effects are asserted. This milestone does not change any already-recovered title frame pixels or invented timing values.

## Private original audio packaging

Use the user's own original CWAV-to-WAV recovery (see C102/C103) and extract/convert the **actual title cue audio**, confirmed against the 3DS source. The C118 private `tools/package_private_ui.py` accepts, in the original private UI folder:

```json
{
  "events": [
    {"frame": 0, "cue": 1},
    {"frame": 1, "cue": 2}
  ]
}
```

Save this as `title_cues.json`, then place the corresponding signed 16-bit, **mono**, PCM, little-endian WAV assets at `title_audio/c01.wav` and `title_audio/c02.wav`. The above is **only a synthetic schema example**, not a confirmed original-game cue sequence. To use the second frame, supply the C117 `title_timeline.json` and independently recovered top/bottom frame images. Without a P3TL timeline, source audio events may refer to frame zero only. The packaging script fails on invalid WAV layout, missing audio, invalid frame indices or durations, bad sample rates and excessive cue lengths. It never creates a default effect.

Private final release validation checks P3TC CRC, frame order, original P3TL timeline agreement, presence of each referenced source PCM asset and P3SA CRC and shape. As before, *presence* alone is not proof the audio was captured from the original game, and the project continues to block a full final release while original gameplay and visual/audio parity are unverified.

## Tests and remaining work

`tests/run_c118_title_audio.sh` runs host-native C loading of P3TC/P3SA with valid and corrupted CRCs, wrong frame counts/order, extra bytes, unsupported PCM rate, oversized samples and reset-on-failure behavior. Synthetic private UI packaging tests exercise original WAV-to-P3SA conversion, timing alignment, missing source assets and invalid cue frame IDs. The private release audit tests original audio presence/CRC and timeline disagreement. Host CI, BlocksDS compilation and DeSmuME startup check the asset-free development ROM, **not actual sound fidelity or full title parity**.

Remaining original content includes the authentic recovered title cue mapping itself, full original title music and transition effects, all cries/audio/voice, shader and model fidelity, every original scene and complete gameplay features.
