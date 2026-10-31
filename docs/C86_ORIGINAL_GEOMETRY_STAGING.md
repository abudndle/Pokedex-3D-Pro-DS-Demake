# C86 — Private original-derived geometry staging and safe UV pairing

This milestone **does not** claim finished 3DS-quality Pokémon models. All Nintendo-derived source files and converted previews are kept in the user's private NitroFS staging archives, not committed here.

## Actual private batch output

- **726/730** source-derived C18 `DS3M v2` model previews validated against the SHA-256 and geometry counts in the recovered private C18 preview manifest. Four source-resource models (`p730`–`p733`) still lack this preview.
- **538** separately packaged, matched `DS3M v2` + `P3UV v1` candidate pairs, sampled from the original recovered model OBJ triangle/UV data: 528 recovered complete C62 UV exports plus 10 earlier inferred C7 UV exports. Each matched pair uses the **same chosen original source faces**, and the candidate triangle counts and 4.12 fixed-point limits were checked. Source-derived UV indices do **not** establish original mesh/material/texture associations.
- **162** original C63 models have *partial* UV recovery, so they deliberately remain untextured fallback previews rather than have invented coordinates; 26 more source previews lack complete UV exports.
- **14** original C18 preview samples used **provisional texture-zero sampled face colors**. The staging pass neutralized those nonverified colors instead of representing them as the authentic 3DS palette.
- The private standalone C86 geometry ZIP contains 726 `preview/` files and 538 `uv_candidates/pNNN.ds3m` + `uv_candidates/pNNN.p3uv` pairs; ZIP CRC and format checks pass.
- A combined private C84+C86 development NitroFS package contains **6,237** files including 726 native model previews, ten source-derived UI pages, the 559-move catalog, the 649-record English Dex text and the 4,039 converted original-derived textures. No P3MT original material mapping exists in this pack.

## C86 public-safe validator

```sh
python3 tools/c86_preview_bundle_audit.py /private/C86_PRIVATE_DS_GEOMETRY_AND_UV_CANDIDATES.zip --require-c86-full-batch
```

The format audit enforces the known model roster (730 records, IDs 0–733 except 721–724), DS3M triangle count and byte length, signed 4.12 coordinate bounds, P3UV version/length, and exact candidate DS3M/P3UV triangle-count pairing. Host CI exercises it using synthetic data only.

## Usage and limitations

The combined private NitroFS package stages **only** 726 fallback model previews as `preview/pNNN.ds3m`, to avoid silently overriding the geometry used by the current game. To evaluate a candidate, place **both** its `uv_candidates/pNNN.ds3m` and `uv_candidates/pNNN.p3uv` into the matching `preview/` location in a test build. **Never copy only P3UV onto a different DS3M.**

The candidate geometry is a maximum 600-triangle source-face sample; it cannot represent the entire higher-polygon 3DS mesh. Original per-mesh material reference decoding, correct texture selection/VRAM allocation, visually faithful animated rendering, missing model exports, and real melonDS/DSi hardware tests remain unresolved. The C85 final-build gate must continue to reject a finished-release claim.

This is a geometry/UV staging milestone, not the end of the project.
