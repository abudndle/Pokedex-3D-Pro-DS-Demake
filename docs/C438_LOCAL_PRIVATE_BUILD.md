# C438 — One-command local private build

`scripts/c438_local_private_build.sh` wraps the existing private-asset steps
(`make check-host`, `tools/validate_original_assets.py`, `make private-qa-rom`)
so a build is one command on an **owner-controlled machine**.

```sh
scripts/c438_local_private_build.sh \
  --nitrofs-zip /private/Pokedex_DS_Private_C141_C148_Asset_Stage.zip \
  --manifest /private/manifest.json --asset-root /private/nitrofs
```

## Guarantees and limits
- Needs BlocksDS and the Wonderful toolchain; exits 3 if they are missing.
- Fails with exit code 2 for a missing option value, missing package, missing manifest, or manifest without `--asset-root`.
- Writes only to `./private/` and the git-ignored `Pokedex3D_DS_BlocksDS.nds`.
  The ROM, stage and reports must never be committed, uploaded to Actions, or
  shared in chat.
- The report records `fidelity_verified: false`. A successful build does **not**
  prove texture mapping, materials, or visual fidelity; run the melonDS and
  hardware gates separately.
- Missing originals fail validation; nothing is substituted.
