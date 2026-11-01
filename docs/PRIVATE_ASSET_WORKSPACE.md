# Private recovered-asset workspace (C18–C98)

This public GitHub repository contains the **source workflow and inventory**, not Nintendo-derived original artwork, models, binaries, or a complete release ROM.

The following archives were located in the project's owner's private ChatGPT file Library on 2026-11-01. They are **not included in Git**, and GitHub Actions' asset-free development ROM cannot render their contents. Keep all packages local/private.

| Recovery | Exact private archive name | Contents / caveat |
|---|---|---|
| C18 | `Pokedex3D_C18_Forms_Models_Provisional_Color_Source.zip` | 726 C18 preview geometry samples; 14 guessed per-face colors are provisional |
| C56 | `Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip` | Original decoded C5 model resources, part 1 |
| C56 | `Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip` | Original decoded C5 model resources, part 2 |
| C56 | `Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip` | Original decoded C5 model resources, part 3 |
| C56 | `Pokedex3D_C56_Decoder_Tools_and_Validation.zip` | Decoder/recovery scripts and validation records |
| C62 | `Pokedex3D_C62_528_UV_Model_Exports.zip` | 528 source-derived UV-equipped OBJ model exports |
| C63 | `Pokedex3D_C63_Partial_UV_Recovery_162_Models.zip` | 162 further **partial** UV model exports |
| C84 | `C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip` | Original-derived GUI, 559 moves, 649 English Dex entries, 4,039 texture files; incomplete fidelity |
| C86 | `C86_PRIVATE_DS_GEOMETRY_AND_UV_CANDIDATES.zip` | Preview geometry and separately staged UV candidates |
| C86 | `C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip` | Private C84 + 726 C18 fallback model previews, **not** verified material binding |
| C98 | `C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip` | Private legacy vs. source-chunked model comparison NitroFS package |
| C98 | `C98_PRIVATE_TOOLS_AND_AUDITS.zip` | C98 comparison support files and audits |

Also available privately: `C86_DS_MODEL_STAGE_REPORT.json`, `C86_COMBINED_PRIVATE_STAGE_AUDIT.json`, `C98_PRIVATE_GEOMETRY_COMPARISON_VALIDATION.json`, and `C98_PRIVATE_COMPARISON_README.md`.

## Private workspace layout

```text
project/
  private/recovery/     # C18, C56, C62 and C63 ZIP inputs (gitignored)
  private/packages/     # C84, C86 and C98 NitroFS ZIP inputs (gitignored)
  private/reports/      # local analyses, hashes and comparisons (gitignored)
  nitrofs/              # unpacked private asset staging; never commit
  tools/
    c86_batch_ds_geometry_stage.py
    c86_combine_private_nitrofs.py
```

## Rebuild C86 previews and NitroFS locally

These commands operate on **your local private copies**, never on GitHub-hosted original assets. A C7 validated OBJ archive is required by the C86 geometry helper's C7 fallback path.

```sh
mkdir -p private/{recovery,packages,reports}
python3 tools/c86_batch_ds_geometry_stage.py \
  --c18 private/recovery/Pokedex3D_C18_Forms_Models_Provisional_Color_Source.zip \
  --c62 private/recovery/Pokedex3D_C62_528_UV_Model_Exports.zip \
  --c7 private/recovery/Pokedex3D_C7_Validated_Geometry_OBJ_Collection.zip \
  --output private/packages/C86_REBUILT_GEOMETRY_CANDIDATES.zip \
  --report private/reports/C86_REBUILT_GEOMETRY_REPORT.json

python3 tools/c86_combine_private_nitrofs.py \
  --base private/packages/C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip \
  --geom private/packages/C86_REBUILT_GEOMETRY_CANDIDATES.zip \
  --output private/packages/C86_REBUILT_COMBINED_NITROFS.zip \
  --report private/reports/C86_REBUILT_COMBINED_AUDIT.json
```

The 528/162 export figures do **not** imply 690 finished textured Pokémon models. C86's UV candidates require paired source geometry and verified material/shader associations; **do not** automatically promote candidates into production NitroFS. C98 comparison assets likewise do not prove original 3DS visual parity.

## Release and privacy rules

- Never commit any of the listed ZIP files, private staging directories, game dumps, converted Nintendo textures/models or screenshot source art to this public repository.
- Run `python3 tools/check_private_release_assets.py --help` and the repository's tests when preparing an asset-integrated build. Keep missing features as explicit blockers.
- All 649 entries, accurate meshes/textures, source sampler roles, original dual-screen UI, animation/audio, 36 challenges and DSi-only AR still need verification; the port is **unfinished**.

## Audit private recovery inputs (C132)

Place the named ZIPs under `private/recovery/` and `private/packages/` according to the table above. The C7 validated OBJ collection is an additional required recovery input. Then run:

```sh
python3 tools/audit_private_recovery_workspace.py --root private --strict
```

This reads local archive metadata and CRCs, rejects duplicate/unsafe ZIP entries, and reports missing or invalid inputs. The public CI does not have access to original assets; `--strict` is for a privately staged asset workspace, not the asset-free CI ROM. No archive is unpacked or uploaded by this audit.

## Recover C56 C5 containers locally (C133)

The following **source-only** tools are now in GitHub: `tools/native_z5_decoder.py`,
`tools/c5_dual_table_parser.py`, `tools/validate_c56.py`, and
`tools/resume_parallel.py`. Their original game input/output bytes and the
private `C56_validation.csv` catalog are **not** in GitHub.

When you have your own private extracted `pNNN.z5` files, place them in
`private/recovery/z5/` and run:

```sh
python3 tools/validate_c56.py \
  --source private/recovery/z5 \
  --decoded private/recovery/c5 \
  --report private/reports/C56_local_validation.csv

# Or recover batches; existing C5 outputs are structurally revalidated.
python3 tools/resume_parallel.py \
  --source private/recovery/z5 \
  --output private/recovery/c5 \
  --workers 4 --limit 50
```

A C56 strict-valid result means only descriptor **structural checks** passed.
The seven source models historically carrying an original C5 descriptor
`0x26` are classified as *warnings*, not verified finished renders.
C56 does not yet assign source-exact UV layouts, material sampler roles,
textures or original Pokémon appearance. C62/C63 recovery and C84/C86/C98
NitroFS staging remain separate, later steps. Keep source dumps, decoded
C5 files and per-model hashes in private storage.

## C134 — C56 source integrity to C86 DS geometry bridge

On 2026-11-01, the three **private** C56 ZIPs and their bundled original
`C56_validation.csv` were inspected against every recovered C5 payload:
**730/730** model IDs matched size, SHA-256, descriptor count and C5 structural
classification; **723 strict-valid** and **7 unresolved 0x26 warnings**:
`p076`, `p077`, `p145`, `p377`, `p391`, `p663`, `p729`.
The C56 model ID inventory intentionally excludes `p721`–`p724`.

Use the source-only local audit to reproduce the verification and join against
the private C86 geometry export report:

```sh
python3 tools/audit_c134_c56_geometry_bridge.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c86-report private/reports/C86_DS_MODEL_STAGE_REPORT.json \
  --output private/reports/C134_LOCAL_C56_C86_BRIDGE.json
```

C86 reports **726/730** fallback DS3M previews and **538/730** paired
UV-geometry *candidates*. The four without fallback DS3M are **p730–p733**.
No matching original C5 material/sampler binding is proven by this join;
**zero production-ready original renderers are certified**. The report is
private; it records every model's structural and preview availability, not a
source-derived copyright payload. Do not merge or publish that private report
or decoded original C5 files into public GitHub.

## C135 — Original-source geometry recovery for p730–p733

The four models that lacked C18/C86 preview meshes have been recovered from
the user's private C56 part-3 decoded C5 archive. The recovered C7 geometry
solver found exactly one valid source candidate per model, with bounds-checked
index groups, finite source XYZ and positive triangle areas:

| Model | Source mesh groups | Original source faces | DS3M v2 preview faces |
|---|---:|---:|---:|
| p730 | 14 | 8,120 | 600 |
| p731 | 13 | 11,518 | 600 |
| p732 | 10 | 11,340 | 600 |
| p733 | 8 | 9,418 | 600 |

`tools/c135_c5_geometry.py` restores the C7 source topology recovery logic
without private binary payloads; `tools/c135_recover_missing_previews.py`
validates the C56 manifest hash, requires unique recovered source topology,
preserves at least one original triangle per mesh group, and converts sampled
original triangles to bounded DS3M v2 geometry.

Private local reproduction requires NumPy for the **C7 research converter**;
the synthetic DS3M and archive regressions can run without it:

```sh
python3 -m pip install numpy
python3 tools/c135_recover_missing_previews.py \
  --c56-part3 private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c86-report private/reports/C86_DS_MODEL_STAGE_REPORT.json \
  --patch private/packages/C135_PRIVATE_DS3M_PREVIEWS.zip \
  --report private/reports/C135_PRIVATE_MODEL_RECOVERY_REPORT.json \
  --base-nitrofs private/packages/C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip \
  --combined-out private/packages/C135_PRIVATE_730_MODEL_NITROFS.zip
```

The private C135 NitroFS pack now has **730 source-derived fallback previews**,
up from C86's 726. Preview triangles are proportional **samples** of original
C5 geometry, not an exact full-resolution mesh. Every added face has the
neutral preview color: **no original UV, shader, material, texture, or animation
role has been inferred.** Neither original 3DS visual parity nor release
readiness is demonstrated. Keep C135 ZIPs and their per-model report private;
only the reconstruction source and synthetic fixtures belong on GitHub.

## C136 — native DS3M header repair and source-paired UV test stage

The native DS model loader reads DS3M header bytes 8–11 as **reserved zero**.
Historical C18/C86/C135 exporters instead wrote original vertex counts there.
That caused every C135 private preview to fail the native loader, even though
asset-free ROM startup and previous archive checks passed.

C136 changes the exporters to write the correct native header. It also
provides `tools/c136_native_uv_stage.py` to repair already-archived private
C135 model previews in place **inside a new output ZIP**, preserving the
original files and recording historical vertex counts in a private report.

The C86 archive has 538 exact DS3M/P3UV candidate pairs. Of these, **49**
have all six signed 4.12 UV coordinates per triangle within [0, 4096] and
C62 source-derived provenance. Remaining **489** pairs require unresolved
repeat/mirror/wrap behavior and are not enabled.

Build the loader-compatible default package (no UV candidates):

```sh
python3 tools/c136_native_uv_stage.py \
  --base private/packages/C135_PRIVATE_730_MODEL_NITROFS.zip \
  --candidates private/packages/C86_PRIVATE_DS_GEOMETRY_AND_UV_CANDIDATES.zip \
  --source-report private/reports/C86_DS_MODEL_STAGE_REPORT.json \
  --mode baseline \
  --output private/packages/C136_PRIVATE_NATIVE_COMPATIBLE_NITROFS.zip \
  --report private/reports/C136_PRIVATE_BASELINE_REPORT.json
```

For an **optional, non-release geometry/UV QA experiment** only, replace
`--mode baseline` with `--mode unit-uv-qa` and use separate output/report
filenames. This replaces BOTH source-derived DS3M geometry and matching P3UV
for only those 49 models, not the unrelated C135 fallback geometry.
No texture manifest, source C5 material associations, original shader sampler
role, wrap mode or palette has been inferred. In the native game these QA
candidate models remain untextured until the existing complete original C5
material/shader provenance gates pass.

A C136 package is **native-header-compatible**, not visually accurate or
proven in a private asset-integrated emulator playthrough. Keep all original
model geometry and conversion ZIPs outside the public GitHub repository.

## C137 — asset-integrated private NitroFS preflight and build workflow

The original C136 baseline/UV-QA ZIPs were inspected **outside GitHub** with
full ZIP CRC checks. Both passed native DS3M and P3PX payload structural
checks: 730 native-valid DS3M previews and 4,039 original-derived P3PX
texture files. The UV QA archive has exactly 49 accepted P3UV companions.
The full original asset packages contain 6,243 baseline entries (6,292
with QA UVs) and approximately 325 MiB of uncompressed private NitroFS
data. Those checks establish **file transport compatibility**, not original
Nintendo 3DS appearance.

The private input is NOT release-complete:
- No original source material reference P3MR, shader capability P3SC, source
  shader words P3SW or verified P3MT mesh assignments for any of 730 models.
- The private pack has P3TX texture manifests for 726 of 730 models and
  P3TM original texture catalogs for 730/730 models.
- Only 10 lower-screen UI pages exist: the upper-screen set, the records
  page, separate title art, original seven-icon HOME touch map and Dex
  transparent upper overlay are absent.
- Original animations, audio, all Challenge modes, AR and source-exact
  UI/gameplay parity remain unverified or incomplete.

Use the **safe, non-release** asset-integrated native build path on a computer
with a working BlocksDS toolchain:

```sh
make private-qa-rom \
  PRIVATE_NITROFS_ZIP=private/packages/C136_PRIVATE_NATIVE_COMPATIBLE_NITROFS.zip \
  PRIVATE_NITROFS_STAGE=private/c137_nitrofs_stage
```

This performs the native-geometry preflight, full ZIP CRC check and
safe extraction, refusing to overwrite an existing staging directory.
It then forces recompilation of a private NitroFS-attached native
`Pokedex3D_DS_BlocksDS.nds` development ROM. Do not commit or share
the resulting ROM or NitroFS files. To test another archive, give it a
different empty private staging directory.

Separately, the release validator `tools/check_private_release_assets.py`
and C137's `--require-release-ready` both reject the incomplete archive.
Running the public source checks and asset-free DeSmuME job is **not**
an asset-integrated boot or visual-comparison result. On the available
local workspace, BlocksDS and melonDS/DeSmuME were not installed; therefore
no source-integrated original-asset ROM or new screenshots can be certified
from the C137 local audit.

For diagnostics without a compiler:

```sh
python3 tools/c137_private_nitrofs_preflight.py \
  --input private/packages/C136_PRIVATE_NATIVE_COMPATIBLE_NITROFS.zip \
  --crc-all --require-preview-ready \
  --output private/reports/C137_PRIVATE_PREFLIGHT.json
```

## C138 — real native C loader preview integration tests

C137 checked ZIP transport and headers, but a structure-only Python check is
NOT proof that the compiled DS native model renderer can load or draw those
files. C138 compiles the actual `source/preview_stream.c` +
`source/model_uv.c` + `source/preview_chunk_stream.c` using the existing
Linux host libnds shim and exercises all 730 preview models individually.

On a machine with a C compiler and the corrected C136 private NitroFS
archive **already staged** in a private directory, run:

```sh
make private-host-probe \
  PRIVATE_NITROFS_STAGE=private/c137_nitrofs_stage \
  PRIVATE_PREVIEW_EXPECTED_UV=0

# For a separately staged C136 49-unit-UV QA archive:
make private-host-probe \
  PRIVATE_NITROFS_STAGE=private/c137_uv_qa_stage \
  PRIVATE_PREVIEW_EXPECTED_UV=49
```

The probe calls the exact `previewStreamLoad()`, `previewStreamDraw()`,
`previewStreamHasUv()`, and `previewStreamUvRangeUnit()` functions for
730 source model IDs. It compares every emitted GL vertex position against
the exact original-derived DS3M XYZ bytes, and every emitted UV coordinate
against its paired P3UV. Unsupported IDs 721–724 must stay unavailable.
Each model must honor its source-triangle count and 600-face preview bound.

**No original content is checked into GitHub:** CI generates 730 tiny
synthetic fixture files, adds 49 synthetic UV files, and exercises the same
compiled original-preview loader via `tests/test_c138_native_preview_probe.py`.
Corrupted headers must fail closed. The private host command needs no
BlocksDS/DS emulator. It is an executable verification of model-loader
transport, **not** an ARM9 runtime test, original textured rendering, or
Nintendo 3DS visual-parity test. Final hardware/melonDS QA is still required.
