# C207 — Private original-source XYZ to P3VX v1

This tool is **source-only**. It never bundles Nintendo files, and it cannot
establish full model fidelity by itself.

For one authorized model, stage `p014.c5` and independently recovered
`p014.obj` **outside this repository**, then run:

```sh
python3 tools/c207_private_c5_xyz.py \
  --c5 /private/source/p014.c5 \
  --obj /private/reference/p014.obj \
  --output /private/geometry/p014.p3vx
```

The output directory must already exist; the output must not already exist.
The converter rejects symlink paths and public-repository destinations, writes
with mode 0600, and does not print private hashes or vertex data.

Acceptance is fail-closed: structurally bounded original C5 primary descriptors
with 28-byte stride are considered individually. For each descriptor, the
converter searches float32 XYZ triples at offsets 0, 4, 8, 12, and 16 within
the record. A descriptor is accepted only when **exactly one** offset gives
finite triples whose float32 values are all present in the independent OBJ
vertex multiset (including duplicate counts). Multiple accepted descriptors
must not reuse the same OBJ vertex occurrences. Only these proven source
descriptors are emitted, preserving their original descriptor IDs; all other
descriptors are omitted. The output may be a **partial model**, never an
automatic claim of complete original geometry. Coordinates must fit signed
4.12; P3VX v1 mesh tables and CRC32 are validated in synthetic native C tests.

The OBJ is *independent comparison evidence*, not a source of output vertices.
No topology, material, UV, shader, skin weight, skeleton, animation, or original
mesh partition is inferred. A P3VX sidecar alone is **not renderable**;
a separately proven, compatible P3IX index stream is required. The existing
C183 private native pair audit and a real asset-integrated emulator test are
still required before any authentic rendering claim.

Run synthetic regressions without private assets:

```sh
python3 -m unittest discover -s tests -p 'test_c207_private_c5_xyz.py' -v
```

Do not upload original C5/OBJ/P3VX/P3IX, proprietary ROMs, private manifests,
SHA-bearing reports, or emulator captures of private assets to public GitHub
or GitHub Actions. For the remaining unmatched models, collect source evidence
rather than relaxing the uniqueness requirement.
