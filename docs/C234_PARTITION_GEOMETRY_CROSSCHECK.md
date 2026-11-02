# C234 — Ordered mesh-partition geometric equivalence

C233 checks a *whole mesh* triangle multiset against private OBJ coordinates.
A whole-model multiset can look identical even when faces are assigned to
different mesh/material partitions. C234 accepts explicit source mesh records
and a triangulated OBJ split by contiguous `g` or `o` boundaries. It
compares each ordered source partition only to the corresponding OBJ group,
using C233's duplicate-XYZ seam handling and winding checks.

Source JSON (PRIVATE, outside public checkout):
```json
{"meshes": [
  {"vertices": [[0,0,0],[1,0,0],[0,1,0]], "triangles": [[0,1,2]]}
]}
```

Run with a privately and independently recovered reference OBJ:

```sh
python3 tools/c234_partition_geometry_crosscheck.py \
  --source-json /private/meshes.json \
  --reference-obj /private/reference-partitioned.obj \
  --report /private/c234-report.json
```

The reference must preserve actual contiguous mesh boundaries in `g` or
`o` order. An OBJ with no labels is one mesh only. Mixed group/object
boundaries are kept distinct rather than silently coalesced. Group names are
not trusted as original identifiers or exported in reports. Inputs are capped
at 64 MiB each, model geometry is capped at 200,000 vertices and 500,000
triangles, and no more than 64 mesh partitions may be compared. Reports
are written outside Git with 0600 permissions and only aggregate flags/counts.
Checks include triangle coverage per partition, seam duplicates, winding,
global DS budgets, and malformed/missing partitions.

**Scope:** A pass proves ordered geometric partition agreement against the
supplied reference, not independent original 3DS mesh identity, 3DS primitive
topology, material IDs, UVs, 3DS render parity, or DS hardware rendering.
In particular, identical/overlapping partitions cannot be independently
identified by geometry alone. No candidate may be promoted to an authentic
source P3IX solely using C234; original C5/C7 source ownership and private
ROM/emulator QA remain gating dependencies. Never commit private model data,
candidate JSON, original OBJ, or ROM/screenshots.

Synthetic validation: `python3 -m unittest discover -s tests -p 'test_c234_partition_geometry_crosscheck.py' -v`.
