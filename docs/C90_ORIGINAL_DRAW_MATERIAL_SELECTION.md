# C90 — Original C5 draw-to-material mapping recovered

## Verified private model scan

All **730** original decoded C5 model containers were scanned. The newly recovered
40-byte original draw table starts at the header's index-descriptor end and is
bounded by its declared record count. Its first 16-bit word stores a source
material selector in the low byte; its next two 16-bit words address the source
vertex and index descriptors. The original draw's face count agrees with the
selected C5 index-descriptor count. Independent C88 material table counts were
used to check every selector.

- **7,116** original draw-to-material index rows passed bounds/count checks
- **3,761** original pass `0x0c02` draw entries and **3,355** pass `0x0c01` entries
- **Two special models** (`p188`, `p659`) have primary mesh descriptors without
  draw entries, so those mesh selectors remain unresolved. Other repeated
  primary draw records (`p236`, `p532`) were unambiguous for their mesh IDs.
- **538** source-UV-matched DS3M/P3UV candidate models independently had
  the original C86 deterministic sampling re-run **byte-for-byte** and were
  assigned source material-index metadata on **322,784 sampled triangles**.
- **Zero** original diffuse/normal GPU sampler-channel assignments verified.
- **Zero P3MT diffuse maps generated**; source materials are not silently
  treated as texture colors. Normal maps may not be bound to body colors.

These references are stronger than name matching: the material IDs come directly
from the original 40-byte C5 draw records and correlate with C88's named original
materials. However, they do not reconstruct full 3DS high-poly animation or
finish the 162 partial-UV and 26 UV-missing models.

## Private original-derived C90 sidecars

The private C90 ZIP contains **538** `source_material_candidates/pNNN.p3mr`
files for the correspondingly sampled original source geometry. Do **not** copy
only the P3MR onto a different model's DS3M: the file does not cryptographically
bind to geometry, and the model must be tested as a matched C86 pair.

P3MR version 1 stores a little-endian 16-byte header:
`P3MR`, version u16, model ID u16, triangle count u16,
range count u16, payload CRC32 u32. The records are 12 bytes each:
first triangle u16, triangle count u16, original material index u16,
first source texture index u16, second source texture index u16,
original draw pass code u16. Each range covers contiguous source-sampled
triangles with no gaps. The CRC guards corrupted sidecar bytes.

The public `p3dSourceMaterialLoad` reader fails closed for missing/oversized/
corrupt files, gaps, wrong model and triangle count, and unknown draw-pass codes.
It does not create P3MT and **cannot be used to authorize textured rendering**.
The public C90 draw-table scanner and synthetic tests run without commercial
assets. The original-derived ZIP and per-model evidence remain private.

## Reproduction and C91 priority

To reproduce the draw inventory using privately provided C56 archives:

    python3 tools/c90_original_draw_material_audit.py --private-root /private/recovered --output-dir /private/c90-results

To reproduce the 538 private paired P3MR sidecars, use the bundled
`c90_original_draw_material_provenance.py` from the user's private C90 tool
package along with the original C75, C86, C62 and C7 archives.

Next, decode **original texture sampler semantics** separately (which original
texture slot is the color map, normal map, shadow map, etc.), then enforce native
DS texture VRAM limits and compare actual screenshots. No end-to-end
original-looking Pokémon model has been certified by this milestone. The C85
gameplay and asset final-release gate remains correctly blocked.
