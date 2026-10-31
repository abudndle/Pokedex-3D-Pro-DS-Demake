# C89 — Original C5 mesh descriptor and C7 geometry pairing

This milestone verifies **source mesh descriptor ↔ OBJ group count/order consistency**, not source GPU material or texture selection.

## Private recovery results

- 730 decoded original C5 models examined; 726 C7 source-derived OBJ exports.
- 3,714 C5 mesh descriptor pairs checked against exported OBJ models; 3,712 matched by descriptor order and exported vertex/triangle counts.
- 725 exported models matched all their mesh descriptors.
- Model p561 has one truncated mesh group and one missing group in its original C7 OBJ export.
- Models p730, p731, p732 and p733 have no original C7 OBJ export.
- **Zero original mesh-to-material links or per-face material ranges verified.** No P3MT material map was emitted.

C5 index-buffer payloads are bounded and their declared triangle counts are checked, but they cannot all be interpreted as ordinary linear vertex indices. The fact that geometry counts agree does **not** prove original face topology, an original GPU material selector, or the correct eye/body texture.

## Run on private original resources

Place the user's three recovered C56 C5 ZIPs and original C7 geometry ZIP in the same private directory:

    python3 tools/c89_mesh_descriptor_join_audit.py --private-root /private/pokedex_recovered --out /private/c89_results

The output CSVs and JSON report contain original-derived names and metadata; keep them private and out of public GitHub. Public code and tests use synthetic fixtures only.

## Follow-up C90

Identify actual mesh material indices from source C5 GPU command/mesh tables and validate each index against C88 source material records. Repair p561 and the four missing OBJ exports from the underlying source geometry only, without inventing UVs or transferring face materials. Only after verified per-mesh references exist can a suitable DS P3MT be created for a matching DS3M/P3UV pair.

The strict C85 original-game release gate remains blocked. Passing a native ROM smoke test does not establish all models' original visual fidelity.
