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
730 source model IDs. It compares every emitted GL vertex position, **per-face RGB color** and
available UV coordinate against the exact private DS3M/P3UV input bytes. Unsupported IDs 721–724 must stay unavailable.
Each model must honor its source-triangle count and 600-face preview bound.

**No original content is checked into GitHub:** CI generates 730 tiny
synthetic fixture files, adds 49 synthetic UV files, and exercises the same
compiled original-preview loader via `tests/test_c138_native_preview_probe.py`.
Corrupted headers must fail closed. The private host command needs no
BlocksDS/DS emulator. It is an executable verification of model-loader
transport, **not** an ARM9 runtime test, original textured rendering, or
Nintendo 3DS visual-parity test. Final hardware/melonDS QA is still required.

### C138 private evidence — host-side native model transport

On November 1, 2026, the Linux x86-64 probe executable compiled in GitHub
Actions was downloaded and executed against two **private** original-derived
NitroFS archives without uploading the original files:

- Corrected C136 baseline package: **730/730** DS3M models loaded and drawn,
  **0** UV companions, exact source XYZ/RGB emission verified.
- Separate C136 C62-source-derived UV QA package: **730/730** models loaded,
  **49** paired P3UV maps accepted, exact source XYZ/RGB/UV emission verified.

Port source tests, source checks, native BlocksDS asset-free development
ROM, ROM verification, and DeSmuME asset-free smoke startup also passed.
GitHub CI publishes a source-only host probe executable artifact named
c138-native-preview-probe-linux-x64; it does not bundle original assets.
These achievements prove the compiled **host** rendering transport accepts
the private source-derived files, not that a private asset-integrated ARM9
ROM has been built or playtested. Actual 3DS reference comparisons,
material/shader provenance, animations/audio and full game parity remain open.

## C139 — fail-closed original-source material and texture binding

The ARM9 model renderer now re-checks **every material draw range** before
binding a DS texture. An original-source C5 face map must assign the same
texture ID to **every face** in that range, the original 3DS material/shader
capability gate must approve a simple color sampler, and the matching
P3UV coordinates must all lie in the safe normalized unit interval. Missing
proof, conflicting face references, out-of-bounds ranges or an invalid
GPU texture ID cause the complete original-derived range to render
**untextured**, without omitting or synthesizing any geometry.

The same check is covered by the synthetic C109/C139 host regression,
run by `sh tests/run_c109_original_material_refs.sh` and GitHub source CI.
This is a defensive integration of original C5 reference metadata, **not**
an inference of shader semantics. The private C136 packages are still
missing original P3MR, P3SC and P3SW provenance files, so this milestone
does **not** imply 3DS-accurate texture output. Recover exact source
material/shader and texture associations before enabling original textures
in an asset-integrated ROM.

## C140 — verified original C5 shader declaration recovery

C140 adds `tools/c140_c5_shader_inventory.py`, a **private-input**
source recovery tool. It reads the original C5 string-table offset from
header byte `0x64`, extracts the contiguous original shader program
declarations and `CF_...` capability flags, and verifies every decompressed
model against its original C56 size and SHA-256 record before accepting it.
It rejects missing/corrupted archives, displaced or duplicated source IDs,
invalid string-table offsets and malformed shader flags.

Locally verified against the user's complete private C56 source packages
on 2026-11-01:

- **730/730** decoded C5 models verified against original C56 SHA-256 records.
- **2,556** original shader declarations recovered, including the original
  `kawa` (1,826) and `shadow` (730) program declarations.
- **1,818** `CF_COLORMAP` occurrences, **1,505** `CF_BUMPMAP`,
  **1,405** `CF_SPECMAP`, **1,527** `CF_SHADOWMAP`, and
  **710** `CF_UVANIM` occurrences. The source contains **92 distinct
  capability combinations**.
- These counts describe *declared effects*, not model-specific material-to-
  shader assignments, verified diffuse samplers, or renderable textures.

Reproduce locally, keeping the JSON report and all C5 payloads **private**:

```sh
python3 tools/c140_c5_shader_inventory.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --report private/reports/C140_PRIVATE_C5_SHADER_DECLARATION_INVENTORY.json
```

This is material/shader **research evidence**, not a complete source
material recovery. The original C5 draw-face-to-material indices and
material-to-shader/sampler references still need to be decoded and
cross-verified against the exact C135/C136 sampled DS3M face order
before producing P3MR, P3SC, P3SW or P3MT. Never generate these production
sidecars from declaration strings or infer that `CF_COLORMAP` identifies
the original diffuse texture by itself. **Zero original textured models
are certified**; the native C139 texture binding gate stays fail-closed.

Source-only tests with synthetic C5 fixtures:

```sh
python3 -m unittest discover -s tests -p 'test_c140_c5_shader_inventory.py' -v
```

## C141 — exact original C5 mesh-group triangle provenance

C140 recovered shader **declarations**, but a shader name or CF_COLORMAP
flag does not reveal the original C5 material-to-face binding. C141
recovers and validates the *separate source mesh descriptor/index-count
boundaries* from all private decoded C5 files and compares their
original triangle counts with the actual C136 native DS3M metadata.

Verified privately on 2026-11-01 from all three C56 archives, checked
against the original decoder validation ZIP's model hashes and status:

- **730/730** original C5 models and native DS3M previews matched IDs.
- **3,759** original C5 index/vertex descriptor mesh groups indexed and
  their source triangle spans recorded without creating fictitious materials.
- **729/730** DS3M source-face-count metadata fields matched the original
  C5 index-descriptor triangle totals.
- **p561** was the sole discrepancy: DS3M declared **2,728** original faces,
  but its original C5 source's seven index descriptors total **3,668**
  triangles. The native preview still has **493** sampled faces.
- An optional, explicit **private-only** package rewrite changed exactly
  the four metadata bytes for `preview/p561.ds3m` from 2,728 to 3,668.
  All actual DS3M vertices, RGB face colors, UVs, textures and all other
  NitroFS entries were byte-for-byte unchanged.
- Re-audit of the private corrected archive reports **730/730** C5
  triangle totals agreeing with native DS3M source-count metadata.

To reproduce locally with owner-provided original-derived assets:

```sh
python3 tools/c141_c5_mesh_provenance.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --nitrofs private/packages/C136_PRIVATE_NATIVE_COMPATIBLE_NITROFS.zip \
  --report private/reports/C141_PRIVATE_C5_MESH_PROVENANCE_REPORT.json \
  --repair-output private/packages/C141_PRIVATE_CORRECTED_SOURCE_COUNT_NITROFS.zip \
  --expected-mismatch p561
```

The expected-mismatch list is mandatory for a repair; unknown differences
fail closed, and an existing output package is never overwritten.
The resulting ZIP still belongs **only in private storage**. It improves
source **metadata correctness**, not texture mapping, model fidelity or
the number of faces actually rendered in DS3M.

**C141 does not equate mesh groups to material groups.** The exact original
C5 face-to-material indices, material-to-shader references and GPU sampler
roles are **not decoded**. No P3MR/P3SC/P3SW/P3MT mapping sidecars or
certified original-textured models are emitted. C139's safe native
binding gates remain disabled for this still-unverified data.

Synthetic regression:
```sh
python3 -m unittest discover -s tests -p 'test_c141_c5_mesh_provenance.py' -v
```

## C142 — efficient, source-hashed opaque C5 track record recovery

This milestone records **79,268 original pointer-indexed C5 track records**
across the same **730/730 SHA-256-verified private C56 models**. Their 16-byte
records hold one source-data pointer and three **opaque** control words.
C142 verifies ascending aligned pointers, nonoverlapping ranges, in-bounds
payloads, per-record source SHA-256, and cross-checks the prior C140 shader
and C141 mesh identity, plus the corrected C141 private NitroFS preview
source-face counts. The recovered records span **59,602,296 private bytes**.
The source record's original material, face, shader, animation and sampler
roles are **not verified**. No P3MR/P3SC/P3SW/P3MT sidecars or textured
renderers are generated from guesses.

To run the reproducible source inspection locally:

```sh
python3 tools/c142_c5_track_index.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c140-report private/reports/C140_PRIVATE_C5_SHADER_DECLARATION_INVENTORY.json \
  --c141-report private/reports/C141_PRIVATE_C5_MESH_PROVENANCE_REPORT.json \
  --nitrofs private/packages/C141_PRIVATE_CORRECTED_SOURCE_COUNT_NITROFS.zip \
  --report private/reports/C142_PRIVATE_C5_TRACK_INVENTORY.json
```

**Faster repeat audits:** add `--summary-only` and use a different private
report filename. This skips hashing and serializing the 79,268 individual
record payloads, while still checking every original archive SHA-256,
per-model track-table boundaries, total track bytes, aggregate track-payload
hashes, C140/C141 identities and native DS3M geometry metadata. It
significantly reduces the large (~41 MB) detailed report.

The host/CI regression uses synthetic source files, including one complete
730-model cross-stage fixture. Run tests **before** GitHub submission:

```sh
python3 -m unittest discover -s tests -p 'test_c142_c5_track_index.py' -v
```

**Speed priority for future milestones:** reuse verified C140/C141/C142
private hashes and summaries; avoid repeating single-model extraction
passes when a bounded batch can inspect all models together. Run host
regressions locally and use GitHub's parallel source and native jobs.
Native texture roles, accurate dual-screen UI, audio, gameplay, and
private ARM9 emulator visuals remain open; an archive audit does not
establish original-game parity.

## C143 — repeated original C5 channel-group candidates

A cross-model analysis of all SHA-256-verified private C56 C5 models
identified **25,956** consecutive groups of three original 16-byte
pointer-indexed records (77,868 of the 79,268 C142 records). Each complete
group uses the **exact ordered control words** `0x00040071`,
`0x00030053`, `0x00030054`; its records share both the original
32-bit owner word and low 16 bits of the second control word.
The remaining **1,400** original records are deliberately left unclassified.
These comprise seven alternative opaque control-code families:

| Unclassified source control code | Records |
|---|---:|
| `0x0402044d` | 767 |
| `0x00010056` | 227 |
| `0x00010c4d` | 222 |
| `0x0002044d` | 93 |
| `0x00030d4d` | 54 |
| `0x0003004c` | 29 |
| `0x0001034c` | 8 |

The repeated groups are *candidates for original transform/animation
channel structure*, not decoded skeleton nodes, rotation/scale/translation
values, timestamps, material IDs, face associations, or GPU sampler roles.
The code never infers material bindings from an apparent channel pattern.

C143 cross-verifies each private input against its original C56 SHA-256
reference and the C142 per-model track count and aggregate payload SHA-256.
Malformed, displaced, mismatched or ambiguous records fail closed.
Original binary payloads and detailed metadata are NOT committed to Git.

```sh
python3 tools/c143_c5_channel_groups.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c142-summary private/reports/C142_FAST_PRIVATE_SOURCE_SUMMARY.json \
  --report private/reports/C143_PRIVATE_CHANNEL_GROUP_SUMMARY.json

# Optional: a separate detailed private report with source record offsets
# and exact opaque control words, not original binary C5 payload bytes.
# Add --detailed and use a different --report path.
```

The summary audit of all 730 private models completes in approximately
3.5 seconds. Repeat validations reuse C142 reference hashes instead of
regenerating the 41 MB C142 per-record report. The 730-model synthetic test
suite checks exact three-code grouping, altered owner/key, malformed pointers,
archive order, and C142 aggregate mismatch.

**Next research dependency:** prove whether these records describe
animation/bone tracks and independently decode keyframe timestamps, values
and skeleton attachment before generating DS animation files. Original
face-to-material indices and shader/sampler bindings remain a distinct,
unresolved investigation; no certified textured model is produced.

## C144 — original C5 timestamped vector keyframe recovery

The source-only `tools/c144_c5_timed_vectors.py` independently decodes the
SECOND and THIRD C5 track records in each exact C143 triplet as little-endian
**16-byte float32 tuples**: `(integer time tag, float X, float Y, float Z)`.
This was verified in ALL THREE original C56 ZIP parts, bound by SHA-256 and
the existing C143 track aggregate provenance.

Private full-roster C144 results (2026-11-01):

| Finding | Verified total |
|---|---:|
| Original C56 models | 730 / 730 |
| Matched three-track channel groups | 25,956 |
| Source `time+float3` streams | 51,912 |
| First vector-stream keys | 298,549 |
| Second vector-stream keys | 626,150 |
| Total validated time+vector keys | 924,699 |
| Paired streams with matching final timestamp | 25,956 |
| Paired streams with identical complete time grids | 19,478 |
| Maximum source time tag | 802 |

Each of the 51,912 streams is finite, begins at **0** and has strictly
increasing non-negative integral time tags. The first control-code payload
has lengths divisible by 10 for 15,444 groups and congruent to 2 for
10,512 groups; its encoding remains **uninterpreted**.

**Important original-data exception:** model `p163` contains three
finite but extreme components approximately `1e10` in one source
time+float3 record. C144 reports these explicitly; they are **not**
converted into a DS animation or trusted as ordinary coordinates.
No source bone IDs, quaternion meaning, component roles, frame-per-second
rate, interpolation, action names or hierarchy have been established.
Nothing is enabled in the Nintendo DS renderer or saved as P3AN yet.

Reproduce locally with owner-only private source files:

```sh
python3 tools/c144_c5_timed_vectors.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c143-summary private/reports/C143_PRIVATE_CHANNEL_GROUP_SUMMARY.json \
  --report private/reports/C144_PRIVATE_TIMED_VEC3_SUMMARY.json
```

For **private forensic inspection only**, add `--detailed-model p000`
and use a separate private output report: includes individual time/value
records for the selected model. The script rejects duplicate/unknown C5 ZIP
members, displaced model IDs, inconsistent C143 track hashes, nonfinite
float values, unordered timestamps and invalid 16-byte stream lengths.
Reports cannot overwrite existing files. CI runs four wholly synthetic
tests, including a full 730-model fixture.

This recovery establishes a valid source data **encoding**, but cannot
claim the original Pokémon skeletal animations have been faithfully ported.
C139 material/shader/texture eligibility remains fail-closed.

## C145 — recover original packed quaternion-like source keyframes

C145 extends the source-verified C143/C144 track decoding to the FIRST
track in each repeating source triplet. Each key is exactly **10 bytes**:
`u16 integer time tag + four biased unsigned u16 quaternion-like values`.
Original words are converted to floating-point candidate components by
`(word - 32768) / 32767`, preserving their original component order without
guessing which element is W/X/Y/Z. All 25,956 source tracks match their
paired C144 float3 streams at the final original time tag.

Private source validation across the 730 SHA-matched original C56 models:

- **4,428,568** original packed quaternion-like keyframes validated.
- **25,956** ordered first-track groups covered (all C143 candidates).
- All packed time tags start at 0, increase strictly and finish at the
  same time as the two float3 tracks; maximum observed tag **802**.
- All decoded quaternion-like values have **squared norm within 0.001
  of 1**, with maximum absolute deviation approximately **0.000123**.
- **10,512** records have an extra two zero bytes for alignment; all
  **21,024** extra bytes verified as zero. Other first streams end
  exactly on a 10-byte record boundary.

This strongly supports a *normalized quaternion rotation encoding*. It
does **not** prove component order, bone ownership, clip/action boundaries,
local/global transform semantics, rotation interpolation, or playback frame
rate. Do not activate source animation in DS or claim source skeletal parity
until the hierarchy/clip binding has been independently established.

```sh
python3 tools/c145_c5_packed_quaternions.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c144-summary private/reports/C144_PRIVATE_TIMED_VEC3_SUMMARY.json \
  --report private/reports/C145_PRIVATE_PACKED_QUATERNION_SUMMARY.json

# Synthetic regression, including a SHA-bound 730-model fixture:
python3 -m unittest discover -s tests -p 'test_c145_c5_packed_quaternions.py' -v
```

`--detailed-model p000` is an optional private-only diagnostic export for
one selected model. Source originals, full keyframe reports, game models
and original animations remain excluded from public GitHub.

## C146 — verified original C5 owner and key-count/time control words

C146 independently cross-checks C143 triplet group control words against
C145 recovered packed quaternion keys and C144 source frame/time endpoints.
For **all 25,956** source group records, the high 16 bits of the second
shared control word exactly equal the first packed quaternion stream key
count, while its low 16 bits equal the common source end-time tag. All
group records share their same original 32-bit owner key.

Across **730/730** SHA-verified original C56 models, the low 16-bit portion
of this owner key is nonzero and **unique within each model**. These tokens
appear in strictly increasing source-record order for **654** models; for
the remaining 76, source ordering differs. **685** models have a first
owner-token value of one. The largest original owner token encountered is
**140**. Neither the token's upper 16 bits nor its relationship to a bone
hierarchy is proven; C146 deliberately does not assume every group is a
distinct bone or generate skeleton parenting indices.

Private reproducible command:

```sh
python3 tools/c146_c5_owner_control_fields.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c145-summary private/reports/C145_PRIVATE_PACKED_QUATERNION_SUMMARY.json \
  --report private/reports/C146_PRIVATE_SOURCE_NODE_CONTROL_SUMMARY.json
```

Optional owner-private `--detailed-model p000` exports every source group
control for a selected model to a different report filename. The script
checks C56/C145 hashes, models and exact Q key totals; malformed control
word duration/counts and duplicate owner tokens fail closed. Four
synthetic regressions include the complete 730-model cross-stage suite.

C146 provides verified **control-word semantics** but not an executable
DS animation rig, shader-to-mesh associations or original C5 sampler
roles. No guessed animations or texture bindings are activated.

## C147 — original C5 named animation transform tracks

This milestone resolves the **high 16 bits of each original C5 owner word**
as an offset into that same C5 model's verified original string table.
It explicitly supports source string *suffix interning*: not all pointers
target the first character of a NUL-delimited string.

Across all three original C56 archives, SHA-cross-checked with C146:

- **730 / 730** original source models validated.
- **25,956 / 25,956** packed-Q/two-float3 triplet groups resolve to
  null-terminated, printable original source node/transform names.
- **25,831** source owner pointers resolve to the beginning of a string.
- **125** point into an existing original string, reusing a valid suffix.
  These are intentional original C5 string-pointer shapes; rejecting
  them as malformed would lose original source node labels.
- Every source track owner name is unique within its original C5 model.
  The record index/token, original name offset and resolved source name
  are exported to a **private** diagnostic report only on opt-in.

```sh
python3 tools/c147_c5_named_nodes.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c146-summary private/reports/C146_PRIVATE_SOURCE_NODE_CONTROL_SUMMARY.json \
  --report private/reports/C147_PRIVATE_NAMED_SOURCE_TRACKS_SUMMARY.json

# To inspect original source node names for a single model privately,
# add --detailed-model p000, using a NEW private --report filename.
```

Four synthetic regressions verify exact node-name mapping, suffix interning,
unsafe/out-of-range pointers, source SHA mismatches and all 730 model IDs.

These source-verified names establish **which original C5 named node is
associated with each packed rotation + vector triplet**. They do **not**
yet provide original parent-child hierarchy, mesh skin weights, clip
transitions/action names or motion interpretation; no skeleton animation is
enabled on DS until that missing data is verified. The source-material
to-shader/texture bindings remain separate and unverified.

## C148 — original C5 skeleton hierarchy and private native P3SK resources

C148 recovers the original C5 node hierarchy table, not merely transform
channel strings. Its start/end offsets are at source header fields
`0x38` / `0x3c`; original node count is high16 of header word `0x10`.
Across all 730 SHA-verified C56 models, table length is **exactly
56 bytes per original node**, without a single exception.

Each 56-byte original record preserves **12 finite float32 matrix
components**, one original parent/type word, and the original
string-table-relative name pointer. The high16 node type is `1`
throughout this verified source collection. The low16 parent field is
`0xffff` for a root; all other parents reference an earlier valid
node index, so the original table forms a verified acyclic node forest.

Private original source validation:

| Recovered source item | Count |
|---|---:|
| Models with validated original hierarchy | 730 / 730 |
| Original node records | 35,840 |
| Root node entries | 4,199 |
| Source parent-to-child links | 31,641 |
| Source C143/C147 named transform tracks tied to exact node IDs | 25,956 / 25,956 |
| Source node names using C5 suffix interning | 137 |
| Largest single-model node table | 148 nodes |

Every C147 animated owner token's low16 matches the original C5 node
table index, and its high16 matches that SAME node record's name offset.
The 56-byte raw affine transform bytes are preserved without
translation/rotation order guesses or resampling.

Export a **private-only** DS-compatible diagnostic NitroFS package
containing one `skeleton/pNNN.p3sk` per original model. P3SK v1 has a
20-byte `<4sHHHHII` header (magic, version, model ID, node count,
root count, name-byte count, CRC32), followed by the original 56-byte
node records and the required prefix of original C5 string-table bytes.
CRC32 covers the complete private record/string payload. Node names
continue to use exact original source string offsets.

```sh
python3 tools/c148_c5_skeleton_hierarchy.py \
  --parts \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip \
    private/recovery/Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip \
  --decoder-bundle private/recovery/Pokedex3D_C56_Decoder_Tools_and_Validation.zip \
  --c147-summary private/reports/C147_PRIVATE_NAMED_SOURCE_TRACKS_SUMMARY.json \
  --report private/reports/C148_PRIVATE_ORIGINAL_SKELETON_AUDIT.json \
  --private-skeleton-zip private/packages/C148_PRIVATE_730_ORIGINAL_SKELETON_P3SK.zip

python3 -m unittest discover -s tests -p 'test_c148_c5_skeleton_hierarchy.py' -v
```

No source original `.p3sk` output is committed publicly. The native
Nintendo DS renderer **does not yet use** these files to deform Pokémon
meshes. Original skinning weights, model vertex-to-bone bindings,
animation action/clip selection and full motion playback remain
unverified and must be completed before claiming 3DS-accurate
animated models. The C139 texture/material eligibility gate is unchanged.

## C149 — native BlocksDS original C5 skeleton loader

C149 adds the **native C** `source/original_skeleton.c` and
`source/original_skeleton.h` to the DS build (automatically picked up by
`Makefile.native`'s wildcard C source list), plus a host-compiled
`tests/c149_skeleton_probe.c` and asset-free Python regression.

For each selected original Pokémon model, the DS runtime can now open its
optional **private** `nitro:/skeleton/pNNN.p3sk` file and validate its
source-verified P3SK hierarchy before accepting it. The loader enforces the
model ID, 20-byte P3SK v1 header, bounded 56-byte original node table,
root/parent topology, exact CRC32, finite source float32 matrix bytes,
printable original string-table names, suffix-interned name references, and
no trailing payload bytes. Missing/corrupt files clear any prior rig and
must not change the native geometry preview.

The loader holds at most **160 nodes** and a **4,096-byte string prefix**,
well above the current private original maxima of 148 nodes and 3,037
string bytes. It retains the original node matrices as exact 48-byte
little-endian source bytes and does **not** infer a transformation
convention or perform skeletal skinning, even when the file is valid.

C149 native host probe was compiled and tested **against all 730 actual
private C148 original P3SK skeleton files**. Verified 730/730 models,
35,840 original node records and 4,199 root nodes. Four additional
synthetic regressions test all 730 model IDs, CRC, wrong model, truncated
file, nonfinite matrices, malformed parents and suffix-named nodes.

To reproduce with owner-private source data:
```sh
# Stage C148's private P3SK files under:
#   private/c149_nitrofs/skeleton/p000.p3sk .. p733.p3sk
make private-host-skeleton-probe PRIVATE_NITROFS_STAGE=private/c149_nitrofs

python3 -m unittest discover -s tests -p 'test_c149_original_skeleton_loader.py' -v
```

The **ARM9 code compiles in the native asset-free ROM** and reads an
optional original owner-private P3SK on Pokémon model selection.
The same private asset-integrated ARM9 ROM is **not yet tested in melonDS**.
Original vertex skin weights, source animation-clip and action selection,
hierarchical bone transforms and 3DS-accurate animations remain unresolved.
The public GitHub repository includes no original Pokémon skeleton files,
model payloads or commercial ROM.

## C152 — private recovery workspace; C84 recovery and C98 absence

The owner-provided, Nintendo-derived recovery packages remain **outside
this public repository, its branches, pull requests and CI artifacts**.
The private working collection is stored in the owner's ChatGPT Library
under `/Pokedex_3D_Pro_PRIVATE_workspace/` with `archives/`,
`recovered/` and `reports/`. Library access is distinct from a GitHub
private repository; the connected account currently exposes only public
GitHub repositories, so original asset payloads must NOT be uploaded to
GitHub. No decrypted original ROM is published.

On 2026-11-01, an exhaustive local inspection found that the exact
`C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip` was absent.
However, **5,510 original-derived C84 content members** (including 4,039
texture P3PX files, ten original-derived upper-screen UI pages, move data
and C84 source SHA metadata) are retained in
`C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip`. The owner-private
recovered ZIP was explicitly labeled
`C84_CONTENT_RECOVERED_FROM_C86_NOT_ORIGINAL_ARCHIVE.zip`: every member
was compared byte-for-byte with its C86 embedded counterpart, and
the C84 source manifest's UI/move SHA-256 entries were independently
checked. This is **not** the identical original C84 compressed archive.
The C84 content is incomplete (lower-screen UI, original effects etc.).

The exact `C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip` is also absent;
only its original private comparison README is available. None of the
remaining NitroFS packages contains the 500 `.p3cs` assets described by
that README. **Do not infer C98 binary content from the README** or
claim that a source chunked/legacy comparison ran.

### Source-only private workspace validator

The GitHub repository includes the portable
`tools/c150_private_asset_integrity.py`. It accepts owner-local original
archives and C140/C141/C143 provenance reports; validates full ZIP CRC,
safe members and SHA-256, and verifies all **730 exact C56 source hashes**,
DS3M native header/count, **4,039 texture P3PX payloads**, **49** paired
unit-safe UV QA companions, **35,840 original P3SK rig nodes** and
**25,956 named C5 animation owner-to-rig bindings**. It also detects 49
legitimate QA geometry replacements versus the old `p561` metadata
exception and confirms the recovered C84 source member hashes.

Place the owner-private ZIP packages in `private/archives/`, the
C84-content reconstruction in `private/recovered/`, and the original
C140/C141/C143 provenance JSON under `private/reports/`, then run:

```sh
python3 tools/c150_private_asset_integrity.py \
  --root private \
  --report private/reports/C152_PRIVATE_CROSS_STAGE_CHECK.json

python3 -m unittest discover \
  -s tests -p 'test_c150_private_asset_integrity.py' -v
```

The private local audit passed all 730 models, with 323,857 sampled
native preview triangles, 3,800,630 original source-triangle metadata
entries, 4,199 skeleton roots, and no source-exact certified texture
binding. Both source-only host-compiled C138 model-loader probes also
passed on private input: 730 original-derived models in each of
the corrected baseline and UV QA packages; 49 actual QA UV pairs.

The owner-provided C56 `validate_c56.py` / `c5_dual_table_parser.py`
were also rerun on the three original decrypted C5 ZIPs. All 730 model
SHA-256 and statuses matched the original manifest: 723 strict-valid,
seven unresolved `0x26`-flag warnings. These are original structural
validation results, **not** claims of original-game completeness.

The SHA-256 sum list, per-file C84 recovered hash list and detailed
source model verification report belong in the private workspace only,
not public GitHub. Further original material-to-shader/sampler bindings,
source skin weights, action-clip semantics, C98 P3CS file recovery,
complete UI, and a private-asset-integrated ARM9 emulator visual test
remain outstanding.
