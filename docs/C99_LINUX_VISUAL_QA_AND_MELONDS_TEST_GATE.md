# C99 — Linux source-model visual QA and real melonDS evidence gate

C99 closes a documentation/testing gap: source-derived Pokémon geometry can be compared at native **256×192** DS screen resolution without claiming the images are from a Nintendo DS emulator. Every screenshot and performance result is labeled by its real capture method.

## Validated private Linux results

- **500 original-derived P3CS model files** decoded successfully via a native Linux GCC C reader, twice (1,000 opens, **1,787,332 decoded triangles**, **2,998 chunks**). The SHA-like rolling decoded-data checksum matches the previous C97 run: `b5c436d393f01d05`.
- Linux build: `cc -std=c11 -O2 -Wall -Wextra -Werror`; host reader **passed**. This is not an ARM `.nds` build.
- Generated six new **256×192 software-rasterized diagnostic frames**, comparing C86 DS3M versus C96/C97 P3CS geometry for source model IDs p000, p001, and p025. The side-by-side montage is packaged privately.
- The three legacy models contain 461, 377 and 420 source-sampled faces respectively. Their high-detail experimental previews each contain 1,800 sampled faces.
- Measured rendered pixel differences using a single deterministic source-projection method: p000 20.80%, p001 14.09%, p025 2.61%. These are differences, **not accuracy or improvement scores**.
- All six output PNGs have valid checksums and 256×192 RGB888 pixels; a Linux-only source screenshot test suite passed **five** local tests.
- High-detail software projection can look fragmented from the selected sparse triangles. This is precisely why source-geometry visual inspection is necessary before claiming faithful models.

## Explicitly not tested

The C99 analysis Linux container did **not** have melonDS, the BlocksDS ARM cross-compiler, or a working external package download. A private original-asset-bearing `.nds` was **not** compiled in this environment, and **zero real melonDS screenshots or DS frame times** were captured. GitHub's earlier asset-free DeSmuME smoke screenshots are not equivalent to this test.

Do not relabel these source-derived software images as emulator screenshots, and do not claim original 3DS texture sampler/shader parity. The C85 strict final-build release gate remains blocked.

## How to run a real Linux melonDS build and capture

Install official BlocksDS for Linux (the Wonderful ARM toolchain plus BlocksDS SDK) and melonDS. The shell helper `tools/c99_linux_build_melonds.sh` accepts a local source checkout and the user's **private** C98 NitroFS archive, checks for required toolchain files, unpacks assets securely into a temporary directory, runs the native development-ROM target, and launches melonDS if available.

```sh
bash tools/c99_linux_build_melonds.sh . /path/to/C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip ./c99_actual_emulator_test
```

Inside melonDS, capture the Dex page in LEGACY mode; press X on Settings to choose HIGH (TEST), return to the same model, capture again, then toggle back and verify that save data is unaffected. Only an actual emulator framebuffer capture may be labeled as melonDS evidence.

For source-only Linux screenshot evidence (private user assets required), the separate C99 private diagnostic tool creates software frames without a ROM. `tools/c99_linux_visual_evidence_audit.py` and its pure-stdlib synthetic regression tests validate PNG integrity and require all report flags to state **no emulator run, no ARM ROM compilation and no original 3DS GPU parity**.

Original Nintendo data, source-derived geometry, images, and private ROMs are excluded from public GitHub. Next C100 target: actual private melonDS runtime capture and hardware frame-time measurements, then fix the visible high-detail surface fragmentation using source topology rather than invented meshes.
