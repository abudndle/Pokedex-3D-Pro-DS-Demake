# Pinned PNG decoder

Upstream: https://github.com/kikuchan/pngle
Commit: `b1c68193f1d3f8642b3e0e095d457a828038e6fb`.
`pngle.{c,h}` and `LICENSE` are MIT licensed, copyright kikuchan.
The included `miniz.c` v1.15 retains its public-domain/unlicense statement;
`miniz.h` is the upstream header-only shim. No binary library is required.

The original source files are retained with these local PNG parser patches:

- Track and reset successful inflater completion; reject IEND before completion,
  compressed trailing bytes and further IDAT data after the stream ends.
- Reject decompressed excess bytes for noninterlaced images.
- Leave bytes after IEND unconsumed for the caller's exact-file-length check.
- Accept legal empty IDAT chunks before or after nonempty image chunks.
- Reject unknown critical chunks instead of silently ignoring them.
- Read big-endian u32 values using unsigned shifts to avoid signed-shift UB.
- Let miniz honor an explicit unaligned-load override; the wrapper disables
  unaligned integer casts on both host and DS for portable C/sanitizer checks.

`source/photo_png.c` compiles this source in one translation unit with gamma
correction disabled (no libm or gamma-table allocation). Old upstream warning
suppression is scoped to included vendor code, not the application wrapper.
The wrapper checks 640x480 limits before feeding IHDR, bounds input to 2 MiB,
rejects interlaced input, verifies ordered/full pixel coverage and completion,
and clears partially decoded output on any failure. No original photos or PNG
fixtures are included in this directory. Synthetic tests exercise actual PNG
pixels, transparency, malformed streams and file-size/dimension limits.
