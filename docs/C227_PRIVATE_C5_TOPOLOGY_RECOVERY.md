# C227 — Private C5 topology recovery batch

A bounded, fail-closed batch tool scans all three C56 decoded-C5 archives and writes candidate triangle-index manifests only to a private output directory outside the public repository. The 0,1,2 / 0,2,3 starting signature is a heuristic, not independent proof of original triangle topology. It uses the existing dual-table C5 structural parser, requires a unique candidate index region after the descriptor payloads, and validates every mesh's vertex ownership, complete vertex references, triangle divisibility, duplicate faces, and manifold edge incidence.

A prior private local research run reported uniquely signature-matched candidate topology regions for 400 of 730 recovered C5 records: 1,146,533 referenced vertices across 1,750 mesh groups and 1,864,085 triangles. An independent re-run against the owner's original three C56 archives verified matching SHA-256 digests, all ZIP member CRCs, the complete 730-model roster, and the aggregate candidate totals above. Of the **330 unresolved records**, **7 failed C5 structural checks** and **323 had no uniquely accepted topology region** under the C227-style signature/layout checks. A prior 243/87 split came from a different exploratory rejection classification and is not the result of this C227 audit. These heuristic results do not prove original triangle order or finished DS-compatible models.

Prior C7 reference comparisons reported matching mesh and triangle counts for two original sample C5 files: Bulbasaur has 3 mesh groups, 2,617 vertices and 4,460 triangles; Ivysaur has 6 mesh groups, 4,103 vertices and 6,548 triangles. The private source SHA and face arrays remain outside GitHub.

Run the synthetic host tests with:

```sh
python3 -m unittest discover -s tests -p 'test_c227_private_topology_batch.py' -v
```

Run the full private batch with the three C56 ZIPs staged outside the checkout:

```sh
python3 tools/c227_private_topology_batch.py --archive-dir /path/to/private-c56 --output-dir /path/outside/checkout/c227-topology
```

Topology alone does not provide vertex positions, texture coordinates, original materials, skeleton weights, animation, or an integrated Nintendo DS render. Keep the generated `topology/pNNN.json` files and source archives private.

Safety and interpretation: ZIP metadata is checked for all 730 models before writing, decompression is bounded per model and in aggregate, the private output directory must be new, and reports are staged with private 0700 directories and 0600 files before publishing. Candidate topology still requires independent primitive-format provenance, vertex/UV alignment, DS triangle-budget conversion and private asset-integrated emulator rendering before it can be called verified original geometry. Synthetic CI contains no private source files.
