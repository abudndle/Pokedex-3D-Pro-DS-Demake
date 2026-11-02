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

Acceptance is fail-closed: a structurally bounded original C5 primary
descriptor with 28-byte stride must have the **same number and order** of
finite float32 XYZ triples as the OBJ vertex records, with per-component
difference at most 1e-6. Exactly one descriptor must match. Signed 4.12
coordinates must fit the DS transport range. A P3VX v1 single-mesh sidecar
with CRC32 is then produced. Descriptor index is reported only as a number.

The OBJ is *independent comparison evidence*, not a source of output vertices.
No topology, material, UV, shader, skin weight, skeleton, animation, or original
mesh partition is inferred. A single-mesh P3VX alone is **not renderable**;
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
