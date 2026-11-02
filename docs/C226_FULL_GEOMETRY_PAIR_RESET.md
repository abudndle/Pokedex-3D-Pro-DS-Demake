# C226 — Full native geometry-pair failure reset proof

C226 strengthens the synthetic native P3VX + P3IX loader regression. Earlier tests checked only selected readiness/count fields after a failed load. The revised probe poisons the complete P3DVerifiedGeometryPair storage before each expected failure and requires every byte to be zero afterward.

Covered failure paths include malformed indices, model identity mismatch, CRC corruption, missing vertex or index files, null path arguments, truncated vertex input, and an oversized vertex file. Each case starts from deliberately dirty prior state so stale coordinates, mesh pointers, buffers, counters, or identity cannot survive a failed load.

The regression uses synthetic fixtures only. It does not inspect or publish Nintendo assets, and it does not claim source C5 topology, original material mapping, a complete original model, or private asset-integrated emulator fidelity.

Run:

```sh
sh tests/run_c178_native_geometry_pair.sh
```

The existing check-host target already includes this native probe, and the BlocksDS workflow compiles the production source. Keep private source model archives, P3VX/P3IX sidecars, hashes and ROM captures outside public GitHub.
