# C277 — Original C5 texture tail candidates (private only)

The 28-byte C5 texture descriptors contain source-relative offsets at +0 and byte lengths at +12. The C277 tool tests whether they cover a contiguous suffix of the decoded C5 file, derives a **candidate** absolute offset by subtracting the descriptor total from file length, and cross-checks every available C73 independently recorded source offset, byte length and SHA-256. It rejects gaps, overlaps, invalid C5 table/name pointers, mismatching C73 anchors, duplicate model ZIP members and over-budget source reads. Private candidate SHA/offset reports are atomically written with 0600 permissions. Public CI uses synthetic bytes only.

A contiguous suffix does **not** by itself prove the original texture payload base, especially for models with no C73 anchors. The tool never marks unanchored missing textures source-verified, does not convert to P3PX, does not infer diffuse/GPU sampler roles, and does not prove original game rendering. Before promoting the four C73-absent models, obtain independent source evidence for their absolute texture payload bases and confirm source texture formats/dimensions, P3PX decode and private asset-integrated emulator results.

Private invocation (paths intentionally generic):

```sh
python3 tools/c277_private_texture_tail_candidates.py \
  --private-root /private/c56 --c73-csv /private/c73.csv \
  --output-private-json /private/reports/c277.json --require-full
```
