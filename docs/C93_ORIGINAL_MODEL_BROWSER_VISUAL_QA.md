# C93 — Original-derived model visual QA in an offline browser

**Private artifact:** a self-contained, approximately 20 MB HTML model viewer
generated from the user's private C92 source-derived diagnostic assets. It
never accesses network resources and is not shipped through public GitHub.

The interface supports model switching across **500 original-derived
diagnostic candidates**, finger/mouse rotation, pitch, zoom, optional wireframe
and background selection. Source-derived 16-bit A1 RGB555 textures are decoded
for the browser with 1-bit transparency and repeat-wrapped source UVs.

## Important improvement for original geometry

C92 DS3M candidates sample at most 600 triangles from each original recovered
OBJ. That deliberately leaves gaps on high-polygon models. In C93, **seven
browser-only reference models** (p000, p001, p003, p004, p005, p006, p007)
are instead reconstructed using the **complete recovered original C7 OBJ face
geometry and UVs**, preserving original mesh order and matching the original
C90 source draw/material selectors. Their faces range from 4,422 to 6,548;
these full-poly assets are **NOT** directly executable on Nintendo DS hardware.
The remaining 493 models still use C92's sampled-geometry preview.

The C93 HTML contains **331,875** total source-derived triangle instances,
**1,152** original-derived candidate color textures, SHA-256 evidence for all
500 embedded compressed/decompressed binary bundles, and per-source DS3M,
P3UV, P3MT, and P3PX checksums. No payload has an unverified material-index
association from a different mesh; the underlying color **sampler channel**
choice is still provisional.

## What was tested

- Private C93 audit rechecked all 500 model payloads and 1,152 texture
  files with **zero** SHA or structural errors.
- Five private Python regression tests passed, including a mutated private
  embedded payload rejected by the checksum audit.
- Headless Chromium with a two-model C93 fixture rendered original-derived
  full-geometry model p000 and changed successfully to p001, reporting no
  JavaScript errors. A screenshot is included privately.
- Public GitHub CI uses only synthetic source/texture fixtures and an offline
  C93 asset provenance validator; no proprietary pixels/meshes are committed.

## Limits and completion status

**This is a visual diagnostic, not a 3DS game emulator, Nintendo DS ROM, or
original shader fidelity certification.** Original GPU sampler-channel
semantics remain unresolved; textures were allocated using source C91/C92
color-name candidates. Some original UV values were inferred during C7
recovery. The source model samples may appear sparse, and low-resolution
textures and software rendering do not reproduce the source 3DS lighting,
bones, skinning, effects, or all original gameplay.

The 38 C92 sampler-review models, 162 source partial-UV models, 26 models
missing complete UV exports, and four source records without archived texture
groups still require further work. The C85 strict final-build release gate
must remain blocked.

## Private invocation

Run the original-derived browser generator only with your local private data:

    python3 c93_build_browser_diagnostic_viewer.py

It reads the private C92 ZIP, private C7 geometry and C90 source-material
evidence and writes a self-contained HTML and SHA256 manifest. No Nintendo
data is uploaded to the public project. The standalone HTML runs locally in
modern browsers that support DecompressionStream(deflate).

The next milestone should extend full source geometry where verified UVs
exist and independently validate GPU sampler/color roles by comparing
source screenshots, while keeping private diagnostics out of the final game.
