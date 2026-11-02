# C227 — Private C5 topology recovery batch

A strict, fail-closed batch tool now scans all three C56 decoded-C5 archives and writes per-model triangle-index manifests only to a private output directory outside the public repository. It uses the existing dual-table C5 structural parser, requires a unique candidate index region after the descriptor payloads, and validates every mesh's vertex ownership, complete vertex references, triangle divisibility, duplicate faces, and manifold edge incidence.

A private local research run against all 730 recovered C5 records found a strict topology region for 400 models: 1,146,533 referenced vertices across 1,750 mesh groups and 1,864,085 triangles. The other 330 records remain unresolved by this particular signature/layout parser: 243 failed descriptor-bound validation and 87 had no unique valid region. These counts are a research result, not a claim that the remaining models have no topology.

The C7 reference tests also pass on the two original sample C5 files: Bulbasaur has 3 mesh groups, 2,617 vertices and 4,460 triangles; Ivysaur has 6 mesh groups, 4,103 vertices and 6,548 triangles. The private source SHA and face arrays remain outside GitHub.

Run the synthetic host tests with:

```sh
python3 -m unittest discover -s tests -p 'test_c227_private_topology_batch.py' -v
```

Run the full private batch with the three C56 ZIPs staged outside the checkout:

```sh
python3 tools/c227_private_topology_batch.py --archive-dir /path/to/private-c56 --output-dir /path/outside/checkout/c227-topology
```

Topology alone does not provide vertex positions, texture coordinates, original materials, skeleton weights, animation, or an integrated Nintendo DS render. Keep the generated `topology/pNNN.json` files and source archives private.
