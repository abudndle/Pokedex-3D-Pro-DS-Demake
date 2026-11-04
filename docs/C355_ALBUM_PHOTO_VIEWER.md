# C355 Album photo viewing

Implements the next bounded Album slice under #227/#1. This branch is stacked
on PR #359 so its tested learnset and save work is preserved. No camera capture,
original photo associations, slideshow or physical DS/DSi parity is claimed.

In Album, A opens the selected `AR_####.png` on the upper screen. The lower
screen displays its name, source dimensions or a clear unavailable state.
Left/Right browses individual photos across seven-file page boundaries; the
visible lower controls support previous/list/next touches. B returns to the
same list selection; a center touch on the view row opens that selection again.
The list viewport scrolls to keep all seven selectable entries visible.
The existing X/A deletion confirmation is available only in the list, never
while viewing. B from the list still returns HOME. Original artwork is restored
when closing the viewer; new controls never infer original artwork hitboxes.

Photo reads use only canonical filenames in the configured Album directory.
Host opens reject symlinks, directories and other nonregular files; O_NONBLOCK
prevents a FIFO replacement blocking before validation. FAT uses regular-file
checks without pretending to provide POSIX symlinks. Viewing never writes a
photo. Existing P3RV saves retain list page/selection: after power-on the Album
list reopens at that selection, rather than automatically opening a photograph.
No save format or original game asset is changed by this feature.

## Bounded image transport

Pinned source [pngle](https://github.com/kikuchan/pngle/tree/b1c68193f1d3f8642b3e0e095d457a828038e6fb)
provides streaming PNG decoding with included miniz; licenses and documented
local parser hardening are in `third_party/pngle`. No external DS binary library
is needed. A single private translation unit disables gamma correction and
unneeded miniz archive/compression APIs. Local patches enforce exact stream
completion, pixel limits, critical chunks and trailing-byte rejection while
allowing valid empty IDAT chunks.

The wrapper reads at most 2 MiB in 1 KiB batches, validates the actual IHDR
before decoder allocation, and accepts noninterlaced images from 1x1 through
640x480. Pixels are scaled with preserved aspect ratio into one aligned
256x192 RGB555 buffer; alpha is composited on black. The streaming decoder uses
fixed inflater storage plus bounded scanline/palette allocations, without a
full source-size framebuffer. Interlaced, oversized, missing or malformed
photos fail closed, clearing partial output and keeping navigation available.
VRAM receives pixels only after the entire image succeeds. ARM9 cache flushing
precedes DMA; diagnostic console writes are suppressed while bitmap VRAM owns
the upper screen. Hardware memory/performance still requires physical tests.

## Verification

`sh tests/run_c355_photo_viewer.sh` checks actual decoded RGB555 pixels,
transparency, palette/Sub filter support, 640x480 downscaling, path safety,
read-only handles, malformed/truncated/oversized streams and navigation bounds.
The initial valid-photo assertion failed before implementation; a legal-empty-
IDAT assertion also failed before the compatibility fix. Existing Album smoke
and synthetic viewer frame/FAT evidence gates are retained.

The C268 workflow runs the existing browse/delete/restart acceptance and a
separate C355 real melonDS session using nine synthetic PNGs. It verifies actual
upper-screen colors, keypad and touch next/previous/reopen, B return, selected
photo persistence, and all nine original fixture files remaining byte-identical.
Its pixel/FAT gates have negative tests; synthetic screenshots alone are never
reported as real runtime evidence. Only genuine CI captures can establish the
emulator result. No original photos, private assets, ROMs or captures are
committed. Asset-free development ROMs remain distinct from original fidelity.
