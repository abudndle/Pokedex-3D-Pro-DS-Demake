# C233 — Seam-aware private geometric face comparison

C228 requires one-to-one vertex identity. Original OBJ exports can duplicate the
same XYZ position for UV seams, so a strict index-to-index comparison may reject
geometrically equivalent triangles when source/reference vertex counts differ.

`tools/c233_seam_geometry_crosscheck.py` compares triangle multisets by unique
reference **XYZ position classes**, preserving face multiplicity and global
winding. Exact duplicate coordinates are grouped; distinct reference positions
within the supplied tolerance are rejected as ambiguous. Missing coordinate
classes, mismatched faces, mixed winding and triangles that collapse after seam
grouping fail closed. Input is bounded by C228; reports use the existing private
0600 writer and contain counts/flags, not source geometry.

Private usage (paths MUST be outside the public checkout):

```sh
python3 tools/c233_seam_geometry_crosscheck.py \
  --source-json /private/c5_candidate.json \
  --reference-obj /private/reference.obj \
  --report /private/c233_report.json
```

This is a **diagnostic geometry equivalence gate**, not an exporter. Even a
passing result **does not verify original 3DS primitive provenance, index
connectivity, UV seam identity, materials, texture samplers, animation, or
native DS rendering**. Do not promote C227/C229 heuristic topology to
source-verified P3IX solely because C233 passes. In particular, C62/C7 OBJ
references are candidate reconstructions and are not independent proof of
original primitive order.

C233's ten synthetic tests cover seam duplicates on either side, differing
vertex counts, winding, false topology matches, near-coincident ambiguity,
degenerate triangles after seam collapse, missing classes, bounded tolerance
and private report permissions. The tests contain no proprietary assets.
