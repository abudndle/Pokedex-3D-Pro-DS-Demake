# C288 — Original material word/draw identity crosscheck

This source-only private gate compares independently collected **C111 original
13-dword material records** (with their record SHA-256 and full source C5 SHA),
**C275 source draw/material/shader/texture reference records**, and **C287
source-SHA-anchored draw-to-texture references**.

The gate rejects missing/duplicate models or draws, mismatched full C5 SHA,
incorrect raw word SHA, shader/material/name/reference disagreement, inconsistent
slot 65535 sentinels, forged GPU sampler verification and unsafe C111 ZIPs.
The CLI writes a bounded private report using the existing C275 atomic writer.

It **does not decode original PICA200 GPU shader instructions or texture-unit
registers**. Original C5 dwords 2–7 and 9–12 remain uninterpreted, and source
texture references are not color/normal/effect sampler identities. A passing
report cannot authorize a native P3PX binding, prove shader equivalence or
substitute for private asset-integrated emulator screenshots.

Offline private usage (never run with proprietary assets in public CI):

```sh
python3 tools/c288_private_shader_material_gate.py \
  --c111-private-zip /private/C111_sampler_evidence.zip \
  --c275-private-json /private/C275_draw_material.json \
  --c287-private-json /private/C287_draw_texture.json \
  --output-private-json /private/C288_crosscheck.json --require-full
```

Next C289 dependency: independently recover actual source GPU texture-unit
commands and shader instruction/texture-coordinate semantics, distinguish
sampler roles without guessing from filenames or capability flags, add a
native fail-closed source-SHA-bound mapping only after that proof, then run
private 730-model asset-integrated native ROM/emulator acceptance. Keep issue
#138 open until original sampler/material binding is genuinely verified.
