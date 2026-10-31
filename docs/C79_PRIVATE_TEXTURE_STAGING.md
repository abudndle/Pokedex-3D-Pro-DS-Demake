# C79 — Private native DS texture staging

The C79 packager accepts the user's private C76 P3TM texture catalogs, C78 P3PX v2 texture ZIP, and C78 original-derived texture metadata CSV. It validates model IDs, per-model file paths, expected texture counts, dimensions, P3PX payload size, per-texture SHA-256, P3TM body checksums and texture ID order. It then builds `materials/pNNN.p3tx` files using the existing native P3TX v1 format.

## Local recovered-asset checkpoint

- 730 model source catalogs; 726 generated P3TX texture manifests, 4 models lack archived source textures
- 4,039 original-derived A1 RGB555 P3PX files validated
- All 726 complete texture collections exceed the viewer's 128 KiB preview texture budget; no **single** texture exceeds it
- 7 synthetic local tests passed; the public GitHub test suite includes additional synthetic regression cases
- C79 private NitroFS staging ZIP includes 4,039 `textures/` files, 726 `materials/` manifests and 730 `catalogs/` files, plus a README; 5,496 entries, ZIP CRC PASS

The ZIP is private, not distributable. Only the clean metadata builder, tests and documentation belong in this repository.

**A generated P3TX says only which source-derived textures belong to a model; it does not prove which texture belongs on any mesh.** The original `.p3mt` mesh/material mapping remains missing. The existing native loader must continue to reject textured rendering without that mapping and original UVs. Do not automatically bind the first texture, discard normal/specular maps, or claim 730 finished visual models.

## Usage

```sh
python3 tools/c79_private_texture_manifest_builder.py \
  --textures-csv /private/C78_TEXTURE_ATLAS_STATUS.csv \
  --pixels-zip /private/C78_PRIVATE_ORIGINAL_DS_A1_TEXTURES.zip \
  --catalogs-zip /private/C76_ALL_730_TEXTURE_CATALOGS_PRIVATE.zip \
  --output-zip /private/C79_PRIVATE_MODEL_SCOPED_P3TX.zip \
  --report /private/C79_REPORT.json
```

Next: decode **verified** original mesh-to-material bindings and build a per-model texture budget selection using only referenced color textures. Then test native DS pixel output and compare against 3DS captures. This is incomplete work.
