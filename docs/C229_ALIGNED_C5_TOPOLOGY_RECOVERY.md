# C229 — Four-byte aligned C5 topology candidate recovery

C227's private C5 scanner recognizes a `0,1,2 / 0,2,3` six-index start signature and concatenates all mesh index groups with no padding. Private comparison with all three authorized C56 decoded-C5 ZIPs showed this was overly restrictive: additional plausible streams start with `0,1,2` and place later mesh index groups on 4-byte boundaries.

C229 preserves **every previously accepted C227 candidate unchanged**, then, only for C227 failures, tries a bounded strict alternative that requires (1) valid original C5 primary/secondary descriptor table geometry, (2) a four-byte-aligned index candidate beginning after descriptor payloads, (3) a `0,1,2` triangle prefix, (4) source descriptor vertex/index counts, (5) valid indices, vertex coverage, no duplicate/degenerate faces and no edges incident to more than two triangles, and (6) precisely one full valid candidate region. It aligns each mesh start upward to four bytes. More permissive source encodings and non-manifold meshes are **not** silently accepted.

A private *aggregate-only* experiment against the recovered 730 original C5 records found:
- 400 C227 legacy candidates, with all 400 original starting offsets unchanged by the alignment-based comparison.
- 287 additional uniquely matching, strict four-byte-aligned `0,1,2` candidates.
- 687 combined candidate model records and 43 unresolved records.

This is **94.1% candidate coverage, not authentic model completion**. Matching plausible index data by byte signature and structural tests is not independent proof of original game topology. C228's independent reference-OBJ mesh equivalence check remains necessary; so do verified source XYZ pairing, model materials, UV and skeleton weights, hardware-aware decimation, private NitroFS rendering and emulator verification.

The public repo contains only synthetic examples and verification code. Private source and generated per-model topology manifests must never be committed or uploaded to GitHub.

```sh
python3 -m unittest discover -s tests -p 'test_c229_aligned_topology_batch.py' -v
python3 tools/c229_aligned_topology_batch.py \
  --archive-dir /path/to/private-c56 \
  --output-dir /path/outside/checkout/c229-private-candidates
```

The batch requires the full 730-entry source roster, rejects unsafe archive metadata, bounds decompression, writes private 0600 reports in a fresh 0700 staging directory and only publishes the output after the whole batch finishes. Summary counts are safe to share; individual topology arrays, model IDs, original C5 source hashes, meshes and ROM files remain private. All candidates have `independent_topology_provenance_verified=false` and `native_ds_rendering_verified=false`.
