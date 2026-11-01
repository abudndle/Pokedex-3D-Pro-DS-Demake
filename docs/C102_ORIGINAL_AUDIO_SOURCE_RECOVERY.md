# C102 — Original Pokédex 3D Pro audio source recovery

The recovered original game audio is **Nintendo 3DS source data**, not a substitute soundtrack and not a Nintendo DS sound engine. All original bytes stay inside the user's private archives.

## Validated private original assets

- **4,407 CWAV** audio containers, **11 CSTM** streams, **1 CSAR** sound archive and **1 CWAR** wave archive.
- Total original source container bytes: **118,320,264**.
- **4,420** structurally checked original container instances; **4,402** unique SHA-256 contents (18 duplicate-content instances).
- Original source CCI headers have the correct magic, little-endian byte-order mark, 64-byte header, bounded canonical section IDs and lengths, nonoverlapping file sections, and bounded file size.
- Every private ZIP member passed CRC and its own source SHA-256 verification. All 5 private synthetic decoder/scanner tests passed; the public test suite adds an output-overwrite protection case.

## Private reproduction

Supply your own lawfully obtained and decrypted original CCI as input:

```sh
python3 tools/c102_original_audio_source_recovery.py --private-cci /private/game-decrypted.cci --private-audio-zip /private/C102_PRIVATE_ORIGINAL_AUDIO_CONTAINERS.zip --private-report /private/C102_PRIVATE_ORIGINAL_AUDIO_SOURCE_REPORT.json
```

The tool uses mmap read-only input and validates each audio container before adding its source-identical bytes to a private ZIP. It refuses to overwrite the input source. No original 3DS audio content, names from commercial archives, or audio samples are checked into this public repository.

## Not yet ported

These original CWAV/CSTM/CSAR/CWAR containers still require verified ADPCM/PCM decoding, original sound-bank/event mapping and a DS-compatible sound stream/mixer with hardware performance tests. The original game's voice, music and Pokémon cry timing must be compared with actual 3DS gameplay, not invented from filenames.

**C102 is a source-recovery milestone only.** It does not change the native DS audio playback path. The C85 final-game release gate remains blocked, and the game must not be described as fully ported.

Next step: classify every recovered stream's codec, sample rate, channel count and loop points from the original INFO records; build a private DS-PCM conversion path only where validated, then implement and test playback in the ARM7 audio subsystem.
