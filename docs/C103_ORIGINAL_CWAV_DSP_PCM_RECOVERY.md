# C103 — Decode original Nintendo 3DS CWAV DSP ADPCM to PCM

C103 is a verified *private audio conversion* capability, not a replacement soundtrack or a Nintendo DS audio engine.

## Source-grounded results

The user's privately recovered C102 archive contains 4,407 original CWAV sounds, 11 CSTM streams, a CSAR and a CWAR. All 4,418 standalone CWAV/CSTM sources use codec ID 2 (Nintendo DSP ADPCM) at 32,000 Hz. CWAV source files: 4,395 mono and 12 stereo; CSTM: 11 stereo looping streams. The codec and channel metadata come from original INFO blocks.

The C103 source-only decoder reads Nintendo CWAV INFO channel references and the original 16 signed DSP coefficients per channel, reconstructs each 14-sample/8-byte ADPCM frame with original predictor/shift and history, clamps to signed 16-bit PCM, then interleaves stereo where applicable. It rejects wrong sections, missing sample data, invalid predictors, unsupported formats/loops, and unbounded sample counts. It does not invent samples.

Five private recovered original CWAV source files were converted and exported to WAV using the original 32 kHz rate. Their PCM SHA-256 digests, frame lengths and nonzero signal amplitudes were independently checked. One sample is stereo (64,012 frames); four are mono (6,733; 4,379; 8,651; 12,143 frames). All source clips and private WAV previews are excluded from public GitHub.

Seven synthetic regression tests cover signed ADPCM nibble decoding, coefficient/history application, malformed stream pointers, truncated samples, codec checks and memory bounds. CI uses synthetic source bytes only.

## Run on privately provided sources

```sh
python3 tools/c103_original_cwav_dsp_to_pcm.py --private-original-audio-zip /private/C102_PRIVATE_ORIGINAL_AUDIO_CONTAINERS.zip --private-preview-dir /private/original_pcm_preview --max-files 5
```

The default five-file output is a *diagnostic*. These samples are not identified as individual Pokémon cries or menu sound effects, because their exact original CSAR sound-event routing has not yet been mapped.

## Remaining for original gameplay

Need sound-event IDs, stream loop context, all original source CWAV/BCSTM conversion, a DS/DSi ARM7 sound playback/mixer implementation, memory and frame-budget measurements, and A/B comparison with original 3DS sound timing and volume. Nothing is marked playback-complete in C80; C85 release remains blocked.
