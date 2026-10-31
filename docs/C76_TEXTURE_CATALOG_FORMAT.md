# C76: all-model texture source staging

The user's **private** C56/C7 archives were inspected locally. A private pack of 730 files named `catalogs/pNNN.p3tm` preserves the 4,039 C75-verified original texture names and raw-source hashes. The pack must **never** be committed to this public repository.

## P3TM v1

All integers little-endian. Header (20 bytes): ASCII `P3TM`, version u16 = 1, numeric model ID u16, descriptor count u16, flags u16 = 0, variable body byte length u32, body CRC32 u32. Each record: texture index u16, width u16, height u16, original opaque format u32, original C5 byte offset u32, original raw-source SHA-256 (32 bytes), name length u16, ASCII source texture name of that length.

The asset-sidecar is read with `p3dTextureCatalogLoad`, which rejects missing, empty, malformed, oversized or mismatched files. This is metadata only: **no mesh-to-material binding has been verified**. It is not a texture upload, DS hardware texture conversion, animation, or a finished model.

## Validation checkpoint

Local archive validation: 730 catalogs, 4,039 original texture descriptors, 7 Python regression tests, native-C loader host test and ZIP CRC pass. The C76 repair queue has 538 ready for original material binding investigation, 162 with partial UVs, 26 missing UV exports and four models lacking original archived textures. Counts are not a claim of complete DS Pokémon models. The source and tests run independently of proprietary payloads; never add commercial assets to public CI.

## Next

Decode *proven* original mesh-to-material references; build a bounded DS texture conversion/upload path and verify appearance in an emulator. Before rendering, reject absent or ambiguous assignments rather than silently pick the first or similarly named texture.
