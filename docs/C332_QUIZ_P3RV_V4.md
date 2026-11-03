# C332 — Exact Challenge question/review resume on DS

## Behavioral acceptance

The previous P3RV v3 checkpoint stored only the chosen Challenge mode, and a reset to Challenge restarted the picker. C332 records the **exact active** question or review at each input-driven state change. The serialized question contains the original PRNG state, question number, score, chosen/correct option, four species options, ten-question unique asked history, source species and clue page. An already scored REVIEW never scores again when resumed; the next user continuation produces the following original seeded question or final results.

The checkpoint also includes the cumulative correct/attempt counters that may be ahead of the separately committed legacy P3SV file following an abrupt power loss. Restoring an active quiz is conditional on that saved state not being older than P3SV and on **P3RC completed-round generation** not having advanced. A stale review cannot cause a previously persisted round to be counted a second time. A completed round writes progress and P3RC before any new quiz can be started, and writes an inactive P3RV v3 checkpoint, preserving backward compatibility.

## Disk representation

All data is little-endian with an exact length and CRC32.

- P3RV v1 (32 bytes), v2 (48 bytes) and v3 (80 bytes) remain readable. Non-active saves still write v3 and retain the older alternating slots, sequence rollover and reserved checks.
- Active v4 is **144 bytes**. Bytes 0–75 are the pre-existing P3RV v3 fields (without its old trailing CRC).
- 76: active=1; 77: stage (QUESTION or REVIEW); 78: mode; 79: question; 80: score; 81: chosen option; 82: correct option; 83: clue page.
- 84–85: current species; 86–93: four u16 choices; 94–113: ten u16 asked species; 114–117: RNG state; 118–121: cumulative answers; 122–125: cumulative correct; 126–129: P3RC round generation; 130–139: zero reserved; 140–143: CRC32 of bytes 0–139.

Invalid stage, mode, identity ranges, duplicate choices, duplicate/invalid asked species, incorrect source association, impossible score/answer count, stale round generation, zero RNG state, nonzero reserved fields, short/long writes and CRC failures are rejected rather than reconstructed using fabricated Pokémon data. The other dual slot can recover if valid. The Pokédex Test mode still requires actual private P3DX text; the checkpoint never embeds original Nintendo names, artwork or files.

## Verification and limitation

- **RED**: [Port source tests 41718043392](https://github.com/abudndle/Pokedex-3D-Pro-DS-Demake/actions/runs/41718043392) failed with `tests/c332_quiz_checkpoint.c:54: Assertion fread(bytes,1,144,f)==144` against the old v3-only writer.
- `sh tests/run_c332_quiz_checkpoint.sh` runs separate host processes for initial question, correct/incorrect answer review, text clue pagination, question ten and result transition, and torn/newest-slot recovery with a recomputed CRC but corrupt option identity.
- `make check-host` includes this regression. Native ROM and emulator gates remain separate.
- Private Nintendo asset-integrated game fidelity, DSi camera support, hardware power-loss testing, and the missing original Challenge modes are **not** established by an asset-free host/ROM smoke test.

If writable FAT/DLDI storage is absent, progress is volatile: the code never claims a durable resume. This is a best-effort non-transactional save design; it improves fail-closed behavior but does not promise prevention of all media or physical flash corruption.
