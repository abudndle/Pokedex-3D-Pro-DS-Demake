# C213 — Original C5 descriptor table bounds

The C172 primitive-coverage gate previously used the u16 field at C5 offset `0x10` as its mesh descriptor count. Private authorized C56 source inspection showed that this is **not** the primary or secondary descriptor count. Those counts are at `0x14` and `0x16`, and the table boundaries are the three u32 values at `0x3c`. For example, one private source model had 3 primary and 3 secondary descriptors while the unrelated `0x10` field was 4. No original bytes, private hashes or per-model payloads are included here.

In a private structural pass over all **730 authorized C56 models**, all **730/730** had structurally valid primary and secondary table extents and bounded descriptor payloads (**3,759 primary and 3,759 secondary descriptors**). The unrelated header field at `0x10` disagreed with the actual primary descriptor count in **560/730** models. These are structural checks only, not original triangle-topology proof. No proprietary data, private per-model hashes or payloads were uploaded.

The C213 gate now validates the original C5 magic, both descriptor table lengths, each claimed mesh's presence in **both** tables, bounded vertex and primitive payloads, source vertex counts and index-count consistency. It rejects a mesh that was previously accepted only because the unrelated `0x10` field was larger than the actual descriptor count.

**This does not decode original primitive topology.** Raw C5 index payloads cannot be treated as plain independent triangle triplets without source verification; a C171 manifest's `verified_by` string is not proof by itself. C211 pair checks, native C179 rendering and private asset-integrated emulator tests remain separate acceptance gates.

Synthetic tests: `python3 -m unittest discover -s tests -p 'test_c213_c5_descriptor_bounds.py' -v`. The full C172/C173/C212 and C211 integration regressions must also pass before merging.
