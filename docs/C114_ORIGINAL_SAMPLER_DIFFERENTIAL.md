# C114 — Cross-file original C5 source proof and sampler-operation differential analysis

## Overall requirement

Port **all of the original Nintendo 3DS Pokédex 3D Pro** to Nintendo DS/DSi, retaining the **original 3DS title screen unchanged**, with original-derived screens, menus, Pokémon materials, animation, audio, data and gameplay. An asset-free development ROM is not equivalent to full-game fidelity.

## Native/asset-bearing build issue fixed

C113 introduced private `P3SW` records holding the exact 13 original C5 words per material. C112 had private `P3SC` shader declarations and C109 had private `P3MR` draw/material spans. Each file independently has a CRC; however **individually valid CRCs are not evidence that all three files came from the same Pokémon or are internally consistent**.

C114 adds a **joint source-provenance audit** for every model for which all three private files are staged. It verifies that:

- `P3SW` and `P3SC` list the **same material count**.
- Each original material's C5 shader index and two C5 texture-reference slots match exactly in the independent `P3SW` and `P3SC` representations.
- Every source C5 `P3MR` draw span references a material in the same model, with exactly matching original texture IDs.
- A changed C5 sampler ID, shader index or draw-material ID blocks release even if all three files have separately correct headers and CRCs.

Missing private sidecars continue to be reported as missing rather than falsely claiming original-asset completeness. The native DS C113 runtime cross-check is retained.

## Original shader-operation differential analysis

`tools/c114_original_sampler_differential.py` reads the **private C111 verified source evidence ZIP**, not guessed texture-name mappings. It independently verifies the SHA-256 of each 13-word original material record, original shader index, and texture-reference slots before grouping by original shader declaration and source texture-reference layout.

Within each source shader group it reports the original C5 word positions (2–7 and 9–12) that vary and which vary between source texture-reference layouts. The known structural fields (word 0 shader index, word 1 texture-reference indices and word 8 name pointer) are **excluded from any unknown GPU operation analysis**.

This is **differential evidence only**. A word's variation or correlation does not prove that it binds a color, normal, specular, environment, or effect sampler. The report deliberately states `original_GPU_sampler_roles_decoded: 0`, `release_ready: false`, and that source shader-instruction disassembly is required. No role assignments are generated and native GPU texture behavior is not broadened without proof.

Run on the game owner's local private data:

`python3 tools/c114_original_sampler_differential.py --private-c111-evidence-zip PRIVATE_C111_SAMPLER_EVIDENCE.zip --output PRIVATE_C114_DIFFERENTIAL.json --require-full`

`--require-full` demands evidence for all 730 original model resources.

## Tests and limitations

The host asset-audit suite builds three separately CRC-valid, synthetic C5 files and confirms that shader-index, texture-reference, C5 face-span, or material-count disagreements are rejected. The differential regression tests source-word SHA-256, unknown-field variation, model completeness and refusal to claim verified GPU roles without source proof. The native BlocksDS ROM/DeSmuME workflow validates the development ROM, not actual 3DS gameplay or private original-material appearance.

**Still not complete:** actual original GPU sampler instruction decoding, authenticated diffuse/normal/effect assignments, source-accurate shader operations, texture-coordinate transforms, all original screens and title visual comparison, models, animation, sound, gameplay and real-private-asset melonDS/hardware parity. C114 changes neither the title screen nor Nintendo's copyrighted assets, which stay private.
