# C151 — Source-verified native original C5 animation track owner binding

The C149 native original C5 P3SK skeleton loader and C150 exact source node
name lookup are already merged. C151 integrates a **read-only original track
owner-to-skeleton binding preflight into native Pokémon model selection**.
This is actual game runtime data integration, not a mock animation.

## Private P3TB v1 format

P3TB is a small **private source-derived** sidecar. Its 20-byte little-endian
header is `<4sHHHHII>`: magic `P3TB`, version 1, original model ID,
original named track count, zero reserved field, CRC32 of the exact private
P3SK node-table-plus-string payload, and CRC32 of the P3TB records.

Each 112-byte `<HHI104s>` record contains the original C5 low16 owner
node index, high16 original name-table offset, original first track record
index, and its exact original source ASCII node name (NUL-terminated,
zero-padded). The runtime checks each original node index, exact name,
original string offset, monotonic source track position, uniqueness, both
CRCs, model ID, padding, bounded size and EOF. Invalid/missing bindings
clear all previous state on model switch. The loaded binding is **not**
used to deform models or synthesize animation.

The source-only private packer
`tools/c151_original_track_bindings.py` verifies SHA-256 of each original
C5 model against C56 and C147 references; verifies each P3SK matches a
fresh source-derived C148 hierarchy byte-for-byte; and then stages
`track_bindings/pNNN.p3tb` into an **owner-private ZIP**. Models with zero
original named track groups get no sidecar. The batch must cover the
full 730-model source roster, and its original track count must agree
with C147. The private ZIP and any private report are never committed.

Example private invocation (paths are user-controlled and not in GitHub):

```sh
python3 tools/c151_original_track_bindings.py \
  --parts PRIVATE_C56_A.zip PRIVATE_C56_B.zip PRIVATE_C56_C.zip \
  --decoder-bundle PRIVATE_DECODER_BUNDLE.zip \
  --c147-summary PRIVATE_C147_SUMMARY.json \
  --private-skeleton-zip PRIVATE_C148_SKELETONS.zip \
  --private-bindings-zip PRIVATE_C151_TRACK_BINDINGS.zip \
  --report PRIVATE_C151_REPORT.json
```

Extract the ZIP into the private NitroFS staging root, preserving
`track_bindings/pNNN.p3tb` next to `skeleton/pNNN.p3sk`. The public
asset-free ROM has no original sidecars; it safely leaves binding inactive.

## Evidence and limitations

Synthetic Linux host tests compile the **actual native C loader** with
`-Wall -Wextra -Werror`, exercise exact and suffix-interned original names,
and reject bad CRC, wrong model, wrong original name, wrong source offset,
wrong node, duplicate owners, out-of-order tracks, trailing data, truncation,
bad padding and stale model-switch state. Synthetic packer tests exercise
source name, owner index, skeleton CRC, and no invented tracks.

**Private 730-model SHA-backed P3TB staging and private asset-integrated
emulator/hardware tests must be reported separately.** Without accessible
private source archives, synthetic tests do not prove all 25,956 real
original owner associations work in the DS ROM.

Not implemented or inferred: original action/clip selection, keyframe
decoding/playback, interpolation, vertex skin weights, hierarchical
transform composition, 3DS GPU effects or accurate full animations.
These remain release-blocking. The unrelated #122 emulator Right/B
navigation validation remains open.
