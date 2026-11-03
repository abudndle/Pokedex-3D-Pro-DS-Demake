# C289 — CRC-bound original-geometry per-vertex UV transport (source-only)

P3VU v1 adds a bounded **optional private sidecar** for UVs indexed by the
exact P3VX vertex/mesh order, rather than assuming that an older 600-face P3UV
preview map applies to independently decoded 1800-face source geometry.

The file carries one model ID, strict packed mesh ID/count/offset table,
an entire-file P3VX CRC32 binding, payload CRC32, and two signed 4.12 UV words
per source vertex. The native loader preflights both CRCs, the existing P3VX
geometry identity, byte-exact EOF, mesh correspondence, and normalized unit UV
range before marking any UV available. Failed loads clear all previous state.
It never searches filenames or tries to guess missing UV data.

Synthetic host regression:

```sh
sh tests/run_c289_native_vertex_uv.sh
```

**Limitations:** CRC32 ties staging files together but is not a proof that
the original C5 UV decoding, C5 shader sampler, repeat/wrap modes or
material-to-P3PX image is correct. There is NO automatic texture activation
and NO original image or converted game data committed here. A private stage
must independently verify original UV vertex order and full C5 SHA
provenance before supplying P3VU; unknown/out-of-unit UVs remain disabled.
Future native draw integration needs confirmed original C5 texture-unit
binding and private melonDS/DSi visual comparison to claim fidelity.
