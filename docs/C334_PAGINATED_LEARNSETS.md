# C334: bounded learnset pages

Implements the learnset infrastructure in #339, beneath original-data milestone
#337 and full-game contract #301. No original records are bundled. Transport
validity and a producer's completeness flag do not authenticate Nintendo data.

The Pokédex's fourth detail tab first tries an optional, privately staged
`nitro:/learnsets/sNNN-fFFF.p3sl`. With a valid sidecar it displays four rows,
learning method/level, and bounded pages. Up/Down and the visible PAGE UP/DOWN
touch row change pages. L/R and the existing touch row still select detail tabs;
Left/Right browse species, Y selects an available form, A toggles favorites,
START/B returns to the entry. Model rendering remains on the top screen.
Up/Down no longer changes animation clips while a detail tab is open.

Without P3SL, the existing P3SD four-reference list is explicitly labeled
"Summary only"; absent original data remains unavailable. Missing P3DM names
display move references rather than invented names. Empty complete lists are
distinct from failed loads. Species/form changes clear the prior list and page.

## Private P3SL v1 transport

All integers are little-endian. A fixed full-list read was chosen over seeking
each page on NitroFS: the entire bounded record can be validated before any row
is published, and subsequent scrolling performs no filesystem reads.

| Offset | Length | Meaning |
| --- | --- | --- |
| 0 | 4 | `P3SL` |
| 4 | 1 | Version 1 |
| 5 | 1 | Exactly 1: producer declares this list complete |
| 6 | 2 | Zero-based National species (0–648) |
| 8 | 2 | Form identity (0–999), exact requested identity |
| 10 | 2 | Row count, 0–256 |
| 12 | 4 | CRC32 of bytes 0–11 followed by all row bytes |
| 16 | count × 6 | Rows: move index u16, method u8, level u8, reserved u16=0 |

Move indices address the existing 559-entry P3DM catalog (0–558). Methods are
transport enums, not asserted original binary values: 1 level (1–100), 2 machine,
3 egg, 4 tutor, 5 evolution (all non-level methods require level=0). Recovery
tools must independently establish the appropriate mapping before staging.
Exact duplicate move/method/level triples, unknown methods, reserved bits,
checksum failures, extra/truncated bytes and oversized lists fail closed.
Different methods/levels for the same move remain valid source distinctions.
The runtime uses about 1 KiB persistent list memory and bounded load scratch.

## Save compatibility

An optional 96-byte P3RV v6 stores detail tab 4 at byte 76, page (0–63) at
77, the complete P3SL checksum at 80–83, and checkpoint CRC32 at 92–95.
Bytes 78–79 and 84–91 must be zero. It is emitted only for an open, loaded
learnset. Normal detail checkpoints remain v5; inactive screens remain v3;
active Challenge remains v4. All v1–v5 readers and dual-slot fallback persist.
Restoration also checks species/form and resets the page if P3SL is missing,
changed or too short. A checksum is integrity evidence, not source provenance.

## Verification boundaries

`sh tests/run_c334_learnsets.sh` exercises real file loading, malformed and
empty/maximal lists, method validation, duplicate rejection, page bounds and
changed-source restoration. `sh tests/run_c334_learnset_resume.sh` checks a
hand-authored v6 checkpoint, native writes, cross-process exact page/checksum,
torn newest-slot fallback and legacy v5/v3 transitions. The original first
v6-load assertion was observed failing before production changes.

The existing C260 workflow additionally compiles a separate synthetic P3SL ROM,
uses actual melonDS keypad and stylus pagination, verifies FAT v6 bytes, and
compares real dual-screen captures across restart. The nine synthetic rows are
test transport data only; they are never packaged as original game records.
Passing host/CI checks does not establish original learnset authenticity,
private-asset integration, DSi camera operation or physical-hardware parity.

Related host-suite repairs: source chunk streams disable stdio read-ahead while
retaining explicit 32-face batches, so draw-time CRC observes edits made through
another file handle on MSYS. The existing draw-time mutation regression failed
before this change and passed after. The FAT duplicate-slot fixture uses a
distinct subfolder so it creates two real files on case-insensitive hosts, and
the texture-alpha test explicitly includes its GL declarations.
