# C339 — Private asset staging for Pokédex 3D Pro DS

The public repository contains **source code only**. A branch of a public GitHub repository is **also public**. Original Nintendo-derived source assets, private game images, and build ROMs containing those assets must remain outside public branches, public PRs, public CI artifacts, and logs.

## Owner-provided archive recovery

The owner's private ChatGPT Library workspace at `/Pokedex_3D_Pro_PRIVATE_workspace/archives/` contains C141 corrected DS preview assets and C148 730 skeletons, plus C84/C86/C96/C98 packages and C18/C56/C62/C63 source recovery archives. C141/C148 can be combined without guessing missing original art.

Run only on an owner-controlled private environment:

```sh
python3 tools/c339_private_c141_c148_stage.py \
  --c141 /private/C141_PRIVATE_CORRECTED_SOURCE_COUNT_NITROFS.zip \
  --c148 /private/C148_PRIVATE_730_ORIGINAL_SKELETON_P3SK.zip \
  --output /private/Pokedex_DS_Private_C141_C148_Asset_Stage.zip \
  --report /private/Pokedex_DS_Private_C141_C148_Stage_Report.json
```

The script rejects malformed ZIP paths, collisions, unsupported symlinks, duplicate file paths, CRC failures and missing 730-model/skeleton roster. The combined stage retains 730 previews, 730 skeletons and private textures. CRC and roster checks do not authenticate original gameplay fidelity.

## GitHub private asset repository

GitHub branch visibility is inherited from its repository: **creating a `private` branch is impossible**. Create a **separate GitHub private repository** under the owner's account (e.g. `Pokedex-3D-Pro-DS-Private-Assets`) with Private visibility *before* any upload. Verify visibility through the GitHub UI or API. Do not create a public repo by accident. Only upload source-owned assets to a private repository the owner controls and only where legally permitted.

Avoid large-file limitations: GitHub regular objects reject individual files >100 MiB; use private Releases, Git LFS, or a private object store where appropriate. Do not put private tokens/asset-download URLs in commits or Actions logs. GitHub Actions on the public ROM repo must not export original-asset ROMs or screenshots.

## Release blockers still open

- Original lower-screen page art including HOME, original title assets on both screens, HOME hotspot mapping and 3D HUD overlay are absent in the inspected private stages.
- The uploaded files include provisional C18 colors, recovered UV and preview candidates; these are not proven fully original 3DS materials or skinning.
- Original audio, game behaviors and DSi AR still require source verification, integration and hardware testing.

Never fill missing originals with fabricated assets and then mark the release gate passed. Asset-free CI may continue separately.
