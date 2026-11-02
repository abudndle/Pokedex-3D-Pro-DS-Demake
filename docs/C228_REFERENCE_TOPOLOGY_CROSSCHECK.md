# C228 — Private independent-reference triangle crosscheck

C227 recovered candidate C5 triangle-index regions using a signature heuristic. A unique signature match does **not** prove that those indices describe the original 3DS mesh. C228 adds a separate face-coverage check against a private OBJ reference, requiring a unique one-to-one XYZ correspondence, identical triangle sets, and consistent face winding. Reordered vertex IDs and globally reversed winding are reported explicitly. Ambiguous or duplicate XYZ, missing/extra triangles, inconsistent winding, invalid indices and nonfinite coordinates fail closed.

The tool operates on **one independently staged mesh** at a time. The source JSON contains `vertices` and `triangles` arrays for the C5 candidate, and the reference OBJ must contain one triangulated mesh with positive global indices. The OBJ must be an independently extracted, authorized reference rather than a copy derived from the candidate indices.

Run with private files staged outside the public checkout:

```sh
python3 tools/c228_reference_topology_crosscheck.py \
  --source-json /private/c5-mesh.json \
  --reference-obj /private/reference-mesh.obj \
  --report /private/c228-result.json
```

The private report is written atomically with mode 0600 and includes only aggregate counts and verification flags, not coordinates or faces. Each input is capped at 64 MiB. The result explicitly distinguishes reference face equivalence from independently established original-game provenance and actual DS rendering. The DS geometry limits (8,192 vertices and 1,800 triangles) are reported but not silently enforced through lossy simplification. No source model, proprietary OBJ, texture, converted geometry, SHA manifest or ROM is committed.

Synthetic regression:

```sh
python3 -m unittest discover -s tests -p 'test_c228_reference_topology_crosscheck.py' -v
```

**Remaining work:** Run against private C56/C7/C62 models with independently verified provenance; resolve C7 mesh segmentation and repeated XYZ seams, generate source-backed DS LODs, then validate native P3VX/P3IX and private asset-integrated emulator rendering. C228's synthetic host tests alone do not complete issue #213 or #156.
