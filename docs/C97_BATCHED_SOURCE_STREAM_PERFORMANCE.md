# C97 — Bounded native source-geometry streaming performance

C97 optimizes the C96 original-derived Nintendo DS geometry-only streaming
reader. It changes **no original geometry, UVs, colors, source model IDs,
material index assignments, or source texture pixels**. It does not activate
the provisional C92 sampler maps.

## Native improvements

- The original C96 `p3dChunkRead` performed **one `fread` for every
  33-byte source triangle**. C97 decodes up to 32 source triangles per
  `fread`, using a fixed **1,056-byte stack buffer**.
- The CRC32 for each source model index and chunk payload now uses a
  **16-entry / 64-byte reflected-CRC32 nibble lookup table**, rather than
  bit-by-bit polynomial iteration. No heap allocation or additional
  model-sized buffers are introduced.
- `p3dChunkOpen` verifies each chunk before marking it renderable, using
  the same bounded 1,056-byte scratch. `p3dChunkRead` continues verifying
  each chunk's original CRC before reporting success.
- Existing DS3M fallback, C96 maximum 1,800 triangles in three chunks,
  per-chunk 600-triangle buffers, and source-color-sampler safety gating
  are unchanged.

## Full private 500-model host benchmark

Two complete scans per execution, repeated five times for each C96 and C97
implementation, using the **same 500 private original-derived C96 P3CS
models** (893,666 source-derived selected triangles per scan, 1,499 chunks):

| Metric | C96 original | C97 optimized |
|---|---:|---:|
| Model open/parse operations (two passes) | 1,000 | 1,000 |
| Decoded original-derived triangles | 1,787,332 | 1,787,332 |
| Checked geometry chunks | 2,998 | 2,998 |
| C `fread` calls | 2,251,074 | 115,228 |
| Requested file payload bytes | 118,035,880 | 118,035,880 |
| Median host CPU time over five runs | 1.247031 s | 0.615260 s |

The FNV-1a digest over all decoded XYZ/UV/RGB values was
`b5c436d393f01d05` in both implementations, for every run. This proves
source data equality across the *private tested* asset set, not original game
visual accuracy.

**Measured call reduction: 94.88%; median host CPU time reduction: 50.66%.**
These figures are from a host libc process on this analysis machine. They
are **NOT** a Nintendo DS fps measurement and do not claim matching 3DS
rendering, hardware performance or missing gameplay parity.

## Validation and reproducibility

The source-only public test `tests/test_c97_batched_chunk_io.py` generates
a synthetic 1,202-triangle P3CS original-like fixture, compiles the real native
source reader, and instruments `fread` calls. It verifies exact decoded
triangles, rejects tampered source geometry and index CRCs, and requires no
commercial game files. The existing C96 source-reader and 600-triangle legacy
DS3M regressions also remain enabled in `make check-host`.

Private batch measurements and the original-derived model ZIP are retained
only in the user's private workspace. Do not upload decrypted original
Nintendo assets, model geometry, textures or user screenshots to public GitHub.

## Remaining prerequisites for the final demake

The private 500-model original-derived P3CS dataset has **NOT** yet been
executed on real DS/DSi hardware or in an emulator with its original assets
loaded. The original 3DS texture sampler channels and combiner semantics
remain unproven; materials stay untextured on the chunked native path. Full
geometry, the other source resources, 162 partial UV cases, original audio,
all Challenges, DSi camera AR and remaining original gameplay features are
unfinished. C85's final-game release gate must remain blocked.

**C98 priority:** produce private, emulator-driven frame-time evidence for
actual source models, then explore source-backed per-range color streaming
only after independent sampler validation.
