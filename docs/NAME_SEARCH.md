# Native Pokémon name search

Search starts in number mode, preserving the existing arrow navigation, A to
open a Pokémon, Y to toggle a favorite, X to open Favorites, L for Move Dex and
R for Settings. Original-art pages keep their existing artwork. SELECT exposes
the text navigation screen.

Tap the mode label on text console row 11, or press L and R together, to switch
between number and name modes. Name mode supports ASCII A–Z prefixes matched
without case sensitivity against names supplied in the private text catalog.

- UP/DOWN chooses a letter, wrapping A/Z; RIGHT appends and LEFT erases.
- L/R cycles previous/next matching Pokémon, wrapping the National index.
- The touchscreen offers letter selection on row 15, erase/append on row 17,
  and previous/next on row 21 (left/right halves respectively).
- A opens the match; Y toggles its favorite status; X opens Favorites.
- Empty and unmatched queries show a clear message and cannot open or favorite
  an old selection. Return to number mode to browse without catalog data.

Prefixes hold at most 12 letters. Query edits retain the current result when
it still matches; otherwise they find the next matching entry. Editing and
matching use fixed buffers and seekable records, without loading all 649 entries
into DS memory. Names containing punctuation or non-ASCII text can be displayed,
but this initial input UI enters only A–Z. Text controls have no hitboxes over
original artwork.

## Private catalog contract

The native build reads `nitro:/dex.p3dx`, packaged from `nitrofs/dex.p3dx` (or
`dex.p3dx` in the explicitly selected private NitroFS directory). This connects
the existing P3DX v1 transport to the native UI; no commercial data is bundled,
created or downloaded. Supply your own privately recovered text to use it.
Missing or malformed catalogs disable name results; numeric browsing still works.

P3DX v1 is an 8-byte header: `P3DX`, little-endian uint16 version 1, then
little-endian uint16 record count 649. Exactly 649 records of 256 bytes follow,
in zero-based National index order. Each contains fixed-width byte fields:
name[32], description[192], height[16], weight[16]. Readers terminate each field
within its buffer. Truncated files and trailing data are rejected, and failed
reads clear the caller's output to avoid displaying a previous Pokémon's text.
Keep this catalog and other original-game payloads out of source control.

Run `sh tests/run_name_search.sh` or `make check-host` for synthetic fixtures,
including malformed catalogs, query editing, wraparound, no-match states,
maximum query lengths and touchscreen boundaries. These tests do not verify
original-game text accuracy or DS/DSi hardware behavior.
