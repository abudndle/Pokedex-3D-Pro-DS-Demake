# C107 — Preserve original Pokémon texture transparency on Nintendo DS

## Verified native upload defect

The C78 P3PX loader accepts two 16-bit original-derived pixel variants:

- **P3PX v1**: legacy direct-color RGB555 samples whose bit 15 is not an opacity contract; native libnds GL_RGB forces an opaque texture.
- **P3PX v2**: direct-color **A1RGB555** recovered texture samples. Bit 15 is the actual retained source opacity (set = visible, clear = transparent).

Previously `p3dDsTextureUpload()` always uploaded through **GL_RGB**. BlocksDS explicitly documents that this mode sets all texture alpha bits to 1 during conversion, destroying transparency from P3PX v2. This can make formerly transparent Pokémon texture regions opaque even if the source model, UVs and material bindings are otherwise correct.

## Native fix

- The bounded private P3PX reader now records the validated source format version alongside width, height and pixel bytes. An invalid or incomplete read resets version and ready state.
- The actual DS GPU upload uses **GL_RGBA** only for v2, preserving the source alpha bit exactly. It keeps **GL_RGB** for legacy v1 opaque textures.
- Invalid/unknown versions are rejected; the existing texture-allocation failure path still deletes the allocated GL ID and reports failure.
- The existing model-scoped texture manifest, material-range and VRAM budget checks remain unchanged. No original source texture data is inserted into this repository.

## Tests

- New `tests/run_c107_native_texture_alpha.sh` builds the **native** (non-C7_TEST_HOST) uploader against a capture-only `nds.h` GL stub, then tests both versions, preservation of source pixels, invalid versions, and GPU allocation cleanup on error.
- Existing P3PX regression now checks source-version propagation and failure reset.
- Normal `make check-host` includes this additional native-upload regression. Public GitHub CI runs native BlocksDS ROM compile and asset-free DeSmuME startup smoke.

## Remaining fidelity blockers

This is a real source-fidelity fix, **not** evidence of correct original Pokémon colors or model-to-sampler associations. C92 material assignments generated from texture color/name hints were explicitly diagnostic and cannot be claimed as authoritative original 3DS GPU draw binding mappings. Correct texture roles/samplers, original source shaders, UV geometry alignment for every form, animation, full gameplay and an asset-bearing melonDS comparison remain unverified.

BlocksDS documents GL_RGBA as the native 16-bit RGB555 plus one alpha bit texture format, while GL_RGB forces opacity and incurs a conversion overhead: https://blocksds.skylyrac.net/libnds/videoGL_8h.html .
