# C272 private diagnostic native ROM isolation

This is an **offline, owner-authorized, diagnostic-only** workflow. It never
uploads Nintendo files, private model bytes, NitroFS trees, SHA manifests,
screenshots or ROMs to GitHub or public CI.

First stage source-derived native geometry with C249 as described in
[the C249 private geometry guide](C249_PRIVATE_GEOMETRY_QA.md). The C249
directory includes a **private** SHA report which must **not** be embedded
into a ROM. Run the new C272 gate on a Linux machine with BlocksDS installed:

```sh
python3 tools/c272_private_rom_build.py \
  --stage /private/c249_nitrofs \
  --output /private/c272_build
```

The destination must not exist, must be outside the public checkout, and is
created with restricted permissions. C272 independently checks the P3SM
diagnostic mapping, source pair identities, mesh/vertex/triangle budgets,
P3VX CRCs and private report SHA-256 digests. It rejects unexpected files,
symlinks, hardlinks, forged source-fidelity claims and inconsistent model
bindings. The clean ROM NitroFS contains **only** `geometry/pNNN.p3vx`,
`geometry/pNNN.p3ix`, and `models/species_map.p3sm`; no JSON reports.
The native build runs in an isolated private source copy, validates ARM9/ARM7
header layout and writes a private ROM plus a private SHA-256 text record.

To verify staging on a machine without BlocksDS, add `--preflight-only`.
This does not build a ROM. C272 synthetic tests in public CI exercise only
the preflight and exclusion boundary, **not** Nintendo models.

A successful build **does not** demonstrate emulator rendering, correct
3DS species-to-resource ownership, UV seams, original material/sampler
bindings, skinning, animations, hardware support or visual parity. Launch
the resulting private ROM in melonDS/DSi where available, capture both
screens, record emulator version and ROM SHA, and compare against authorized
original references **privately**. Do not upload the private ROM or captures.
