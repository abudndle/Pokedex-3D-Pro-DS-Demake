# C109 — Verified original C5 draw-material reference gate

The goal remains a faithful port of **all of Pokédex 3D Pro** to Nintendo DS/DSi, using the user's private original game assets, original presentation, behavior and data. This milestone is a strict source-reference check, not a completed Pokémon renderer or a claim that all GPU samplers have been decoded.

## What changed

C90 recovered a private CRC-checked **P3MR** sidecar from original C5 3DS draw tables, covering preview triangle spans with source material indices and the two texture-reference IDs recorded by that original material. C108 already checked that candidate P3MT ranges covered the DS preview mesh with valid texture records, but could not distinguish source-backed references from C92 experimental texture-name hints.

C109 requires both facts before any native Pokémon texture upload:

1. The loaded original-derived DS3M mesh has a corresponding, valid P3MR file in **nitro:/materials/pNNN.p3mr**, with matching model ID and triangle count, primary original draw pass and valid source CRC.
2. Every candidate P3MT material range lies entirely within a source P3MR material span, has that **original C5 material ID**, and references one of its actual source texture slots (never 65535/no-texture).

A material range crossing an original C5 material boundary or choosing a texture ID that is present in P3TX but absent from the corresponding original C5 material is rejected. Missing, corrupt or mismatched source provenance results in a deliberately **untextured** native model preview rather than an invented texture placement. Runtime loading continues to be limited to existing DS3M preview models, with native P3CS high-detail source chunks remaining untextured pending source-aligned sampler validation.

The private final-release asset auditor now requires a source P3MR file for every expected resource model and validates its header, model ID, triangle coverage and CRC. Both the C109 native host fixture and release audit tests use entirely synthetic 3DS-like records.

## What is **not** established

The **original 3DS GPU diffuse/color sampler role is still not verified**. An original material can reference two textures, either of which might be non-color data. This source-reference validator checks that a candidate belongs to the original material but **does not identify which slot is used for final color**, decode shader semantics, confirm UV transformations, or prove the C92 diagnostic bindings are visually accurate. It never marks such mappings as verified end-to-end.

Further source shader/sampler tracing, private real-asset screenshots from melonDS, original animations/texture/material fidelity, audio, interface fidelity and all gameplay parity are still required. No proprietary Nintendo payload is committed to the public repository.

## Regression testing

Run: `sh tests/run_c109_original_material_refs.sh`. The host fixture loads actual P3MT, P3TX and original-style P3MR structures, verifies matching source ranges and rejects wrong texture IDs, nonoriginal material IDs, crossing spans, corrupt CRC, truncated files, incorrect model IDs and missing references. This test is also in `make check-host`.
