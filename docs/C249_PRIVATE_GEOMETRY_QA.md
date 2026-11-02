# C249 private native geometry QA NitroFS

This is a **diagnostic-only** path for exercising source-derived P3VX/P3IX
geometry in the real ARM9 loader. It does **not** recover the 3DS
species-to-resource mapping, UV seams, materials, original skinning, animation
or visual fidelity. Do not publish the staged NitroFS, original inputs, hashes,
private ROMs, or screenshots.

## Local usage (outside the public checkout)

Stage validated P3VX/P3IX pairs as `pNNN.p3vx` and `pNNN.p3ix` in a
private input directory. Create a **private** JSON mapping file with explicit
diagnostic Pokédex slots (1-based species, 0-based model/resource ID):

```json
{"purpose":"diagnostic","assignments":[{"species":1,"model":2}]}
```

This example is **not an authentic species binding**. Never infer resource
identity from Pokédex order. The tool refuses other mapping purposes rather
than pretending to authenticate user-supplied species provenance.

```sh
python3 tools/c249_private_geometry_nitrofs.py \
  --source-dir /private/pairs \
  --mapping-json /private/diagnostic_slots.json \
  --destination /private/c249_nitrofs
make -B -f Makefile.native NITROFSDIR=/private/c249_nitrofs rom
```

The tool compiles the actual C179 host GL draw probe once, validates every
requested pair against native mesh/index/CRC/budget rules, runs the probe for
each model, and publishes only if **all** pass. The output contains
`geometry/pNNN.p3vx`, `geometry/pNNN.p3ix`, the runtime-readable
`models/species_map.p3sm`, and a **private** SHA-256 QA report.
The output directory must not already exist. Files are created mode 0600,
directories mode 0700. Input symlinks, hardlinks, invalid model IDs, duplicate
species slots and corrupt pairs are rejected. This is not a production
original-asset release gate.

The source test `tests/test_c249_private_geometry_nitrofs.py` uses only
synthetic geometry. Public CI builds an asset-free development ROM; it cannot
prove any of the private pairs render in DeSmuME, melonDS, DSi mode or hardware.
Private ROM QA must separately record ROM SHA, model/resource mapping evidence,
real dual-screen captures, and exact emulator/console results.

**Next evidence requirement:** recover independently sourced species/resource
identities, stage the 25 currently native-budget-fitting candidates with
explicit diagnostic slots, then run a private asset-integrated emulator
playthrough and compare against authorized original references.
