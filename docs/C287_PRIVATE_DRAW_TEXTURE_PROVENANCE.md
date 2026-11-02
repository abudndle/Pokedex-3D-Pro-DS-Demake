# C287 — original C5 draw/material to source texture SHA provenance (private)

C287 adds a **full original C5 model SHA-256** to the C279 descriptor report and requires that it match the C275 original draw/material report for the same model. It then joins original C275 draw/material reference slots to C279 original texture descriptors (source SHA-256, original opaque format word and C73/P3TM corroboration), and optionally to C286's conversion-consistent low-bpp candidate. This prevents accidentally combining a draw from one original model dump with textures from a different source. The private output preserves original draw, mesh and material IDs, reference names and hashes; it does not infer GPU texture units.

The two C5 texture-reference fields in C275 are **source declarations, not verified GPU sampler slots**. A source reference with no C73/P3TM anchor stays unverified; a source-anchored texture without a low-bpp C286 record remains source-anchored without a decoder hypothesis. A C286 candidate must match the C279 original texture SHA and opaque source format. A source reference index of 65535 is treated as absent, not a default texture. Forged GPU sampler/native P3PX verification flags are rejected.

Run privately after regenerating C279 with the new C5 model SHA field and producing C275 and C286 reports from the **same authorized C56/C84 inputs**:

```sh
python3 tools/c287_private_draw_texture_chain.py \
  --c275-private-json /private/reports/c275.json \
  --c279-private-json /private/reports/c279.json \
  --c286-private-json /private/reports/c286.json \
  --output-private-json /private/reports/c287.json --require-full
```

All private JSON inputs are bounded, regular, non-symlinked single-link files; output is atomic mode 0600 through C275's private writer. Public CI uses synthetic reports only. The 12 C287 tests and C279 source-SHA regression cover identity, index bounds, missing references, candidate provenance and forged verification flags.

**Not yet verified:** no actual 730-model C287 private report in this run, no independent PICA200 sampler/texture-unit commands, no native verified original material-to-P3PX binding, and no private asset-integrated DS/DSi visual acceptance. Issue #138 remains open. Next C288: independently recover sampler/texture-unit command semantics from authorized original sources, design a bounded native binding transport with explicit proof, and validate on private hardware/emulator captures.
