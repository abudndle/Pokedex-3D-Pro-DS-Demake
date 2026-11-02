# C211 — Private source-geometry pair preflight

The existing C207 exporter derives P3VX vertex coordinates only from uniquely matched original C5 float32 XYZ descriptors and an independently recovered OBJ vertex multiset. The C173 exporter derives P3IX indices from a C171/C172 primitive-evidence manifest. **A manifest's claimed `verified_by` field is not itself independent proof of original topology.** Confirm its provenance separately.

C211 checks that a staged P3VX exactly matches the C207 output and that P3IX exactly matches the C173 verified-manifest export, then validates the *pair* against native DS constraints: matching model IDs, P3VX CRC, sorted mesh IDs 0–63, packed vertex ranges, each P3IX mesh's vertex ownership, nondegenerate triangles, at most 8,192 vertices and 1,800 triangles. It rejects mismatches rather than inventing a mesh mapping or simplifying original topology.

For one privately staged authorized model (all paths outside the public checkout):

```sh
python3 tools/c211_private_source_pair.py \
  --c5 /private/source/p000.c5 \
  --obj /private/reference/p000.obj \
  --manifest /private/evidence/p000.json \
  --p3vx /private/geometry/p000.p3vx \
  --p3ix /private/geometry/p000.p3ix
```

No private asset or hash is emitted. The command prints only model/mesh/triangle counts and explicit false completion flags. The original C5/OBJ files, P3VX/P3IX, evidence manifest, SHA-256 reports, private ROM and captures must never be committed to public GitHub or CI artifacts.

Synthetic-only regression:

```sh
python3 -m unittest discover -s tests -p 'test_c211_private_source_pair.py' -v
```

**Remaining acceptance:** independently prove the original C5 primitive order for each mesh, then run the native C179 probe and private NitroFS asset-integrated DeSmuME gameplay, verify original mesh partition/material/sampler, skeleton/skin weights, action/clip playback and complete dual-screen rendering. Passing this gate is neither full-model provenance nor emulator visual fidelity.
