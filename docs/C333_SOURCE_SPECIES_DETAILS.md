# C333 — Original-source species details: safe transport and remaining recovery

## Actual source inventory, not a completion claim

**Verified existing native source formats:**
- `nitro:/data/dex_en.p3dx` (P3DX v1) has 649 fixed 256-byte records; the native loader reads **name, description, height, weight**. It does **not** encode HP/attack/defense, abilities, evolution graphs or learnset methods/levels in those records.
- `nitro:/moves.p3dm` (original-source 559-record P3DM) has names/descriptions/effects. Its move index is the only present verified native link target; it is not proof of which Pokémon learn a move.
- `nitro:/models/forms.p3fm` maps independently verified form resources. A form's source-verified stat metadata cannot be inferred from a mesh.
- The user's previous C18 handoff explicitly lists original per-species stats, types, abilities, evolutions and learnsets as **remaining unrecovered**. The authorized decrypted game archive and a verified per-entry stats/ability/evolution/learnset mapping are not accessible in public GitHub CI or the current file workspace.

**Consequently:** this milestone implements an *optional, fail-closed* species/form metadata viewer and private-data transport. It does **not** assert that authentic original Pokédex 3D Pro stats and ability/evolution/learnset values have been recovered or that 4 move references are a complete learnset. C333 must remain an **open original-content verification milestone** until the private archive is audited and integrated.

## Optional private P3SD v1 record

An exact **64-byte** file, with CRC32, named `nitro:/details/sNNN-fFFF.p3sd`, with zero-based National species 000–648 and independently verified form 000–999. A source exporter must resolve original 3DS record identity and prove form mapping; the parser does not infer it. Only privately authorized generated P3SD records should go under `NITROFSDIR/details/` during private builds.

| Bytes | Meaning |
|---|---|
| 0–3 | literal `P3SD` |
| 4 | version 1 |
| 5 | bitmask: 1=stats, 2=abilities, 4=evolution targets, 8=move references |
| 6–7 / 8–9 | zero-based species / form, little-endian u16 |
| 10–12 | number of ability IDs (max 3), evolution target species (max 2), move references (max 4) |
| 13 | zero reserved |
| 14–19 | six base stats, HP/Atk/Def/SpA/SpD/Spe; all positive only when the stats bit is set |
| 20–25 | 3 u16 ability IDs; numbers only, no unverified ability names |
| 26–29 | 2 u16 evolution target species, 000–648, distinct, no self edge |
| 30–37 | 4 u16 original P3DM move indices, 000–558, distinct |
| 38–59 | zero reserved |
| 60–63 | CRC32 over bytes 0–59 |

All unused array elements must be zero; missing field groups have zero counts and payloads. An exact file length, CRC and valid ranges are required. A valid CRC is **not** Nintendo-source authentication; provenance must be audited separately. The native DS view displays “Original detail unavailable” for absent or corrupt sidecars and does not invent Pokémon species data. Source-backed move names use the separate original `P3DM` catalog only when available. The v1 move reference array is deliberately a bounded small summary, not a claim of complete Gen V learnset parity.

## UI, save and regression behavior

- On a Pokédex entry, **START** opens the details in the bottom screen while the existing 3D model remains on the top screen. **L/R** or the visible lower-screen tab band cycle stats / ability IDs / evolution targets / bounded move references. **START or B** returns to the entry. **LEFT/RIGHT** still browses national entries; **Y** still cycles verified existing forms; **A** retains favorite toggling, and **X** still enters original text Search.
- The detail screen forces the fallback text layer even when a page has private 3DS artwork; unverified original image touch hitboxes are never fabricated. The original artwork is restored on exit.
- P3RV **v5 (96 bytes)** stores the active Pokédex detail tab in byte 76, reserved 77–91=0, CRC at 92–95. The existing v1/v2/v3 non-detail saves remain loadable; the v4 active Challenge restore remains independent and intact. Inactive, non-quiz checkpoints still write v3 (80 bytes).
- Host regression `tests/run_c333_species_details.sh` validates missing/form-mismatched/oversized/short/CRC-corrupt records, identity ranges, flag/count coherence, duplicate targets/moves and unknown reserved bytes.
- Host regression `tests/run_c333_detail_resume.sh` proves cross-process exact-tab restoration, previous valid-slot fallback after a CRC-correct but reserved-invalid newest record, and return to v3 after leaving details.
- Real emulator acceptance: `C333_DETAIL_ONLY=1` invokes official pinned melonDS 1.1 DLDI/FAT, opens details via START, verifies the v5 slot, restarts the actual emulator and compares the lower-screen pixels. This does not assert Nintendo data is present in an asset-free ROM or prove DSi hardware.

## Remaining necessary original-data recovery

1. Locate and privately audit the user's authorized decrypted source archives with SHA-256 manifests. Determine **whether** original stats/ability/evolution/learnset fields are actually encoded in this 3DS title, or if only the UI uses external canonical Pokémon data. Preserve raw origin, binary offsets, version and language/form mapping.
2. Establish independent semantic checks on each 3DS original record or source-stable mapping, including alternate forms, abilities, evolution triggers, learn levels and game-specific semantics. **Do not** copy community databases into the original-game slot or claim such data was decoded.
3. Extend this bounded v1 transport and viewer only for additional verified fields; it currently covers up to four move references, not a full learnset or evolution conditions. Verify all 649 National species plus source forms in private integration and compare visual UI against the 3DS.
4. Keep decrypted Nintendo data, original ROM and private P3SD payloads outside the public repository, its Actions artifacts and Logs. The release-complete gate must remain blocked without original-source and physical DS/DSi parity checks.
