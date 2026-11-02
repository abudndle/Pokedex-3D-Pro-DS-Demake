# C286 — C5 source format-word consensus across private C279/C285 reports

C286 connects two **previously independent, private, SHA-backed evidence layers** without loading Nintendo pixels into public CI. C279 provides original C5 texture descriptor order, source SHA-256, original opaque format words and C73/P3TM corroboration; C285 supplies pixel-exact candidate decoders consistent with the prior C84 converted P3PX. For a repeated `(opaque source format word, storage bits-per-pixel)` group, C286 can narrow an ambiguous C285 candidate **only when at least one member has exactly one matching candidate** and every other candidate-bearing member admits that same candidate. Conflicting unique candidates fail closed; all-ambiguous groups remain ambiguous. C286 never guesses a GPU format from the word itself.

C286 does **not** establish an independent PICA200 GPU format specification, sampler/alpha/tile state, original draw/material-to-texture-unit assignment, exact original shader behavior, or DS/DSi rendering parity. Agreement with C84 is conversion consistency, not independent original visual proof. The private JSON contains source SHA values and must remain outside public GitHub, Actions artifacts, and distributed ROMs. Only synthetic fixtures are committed.

Private-only invocation (requires C279 and C285 reports generated from the same authorized original C56/C84 set):

```sh
python3 tools/c286_private_format_consensus.py \
  --c279-private-json /private/reports/c279.json \
  --c285-private-json /private/reports/c285.json \
  --output-private-json /private/reports/c286.json --require-full
```

The input gate rejects unexpected models, duplicate texture indices, malformed SHA strings, missing C73/P3TM corroboration, mismatched source storage density, invalid candidate names, contradictory status, symlinked or hardlinked private inputs, and reports over 32 MiB. Output is an atomic 0600 private report through the existing C275 writer. Aggregate-only stdout reports narrowed/remaining ambiguity and conflicting format-word groups; the tool never prints model names or private hashes.

**Acceptance:** Twelve synthetic host tests; full C279/C285 private reports required for actual 730-model counts; native BlocksDS ROM/header and asset-free DeSmuME remain separate checks. No private C279/C285 reports are available in public CI, so no numerical narrowing is claimed until a genuine private run is completed. The next independent task is source-backed texture-unit/sampler command extraction, draw-to-material binding, and private asset-integrated native/emulator visual QA. Issue #138 stays open.
