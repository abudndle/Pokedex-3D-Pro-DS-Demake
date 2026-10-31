# Pokédex 3D Pro — Nintendo DS / DSi Demake

Community research and source-level demake project. **Unfinished. Not a verified playable ROM.**
this is ai project dont look into this page please i was originally trying to keep it private but i cant do that 
anynore so dont mind the notes and messages you read in the code
im just playing with ai for fun

## Goals
- Preserve the original game's menu layout and recovered model geometry rather than substitute arbitrary lookalikes.
- Support all non-camera features on DS, DS Lite, and DSi.
- Keep camera-dependent augmented reality exclusive to DSi, hidden on DS/DS Lite, and implement it last.
- Verify touch controls, original asset rendering, save compatibility, and melonDS boot behavior.

## Recovery status (last checkpoint C63)
- 730 original indexed model binaries previously recovered and decoded into C5 containers.
- 528 new OBJ exports from whole-model UV recovery (C62).
- 162 additional partially UV-recovered model exports from mesh-level matching (C63).
- UV recovery is **not** equivalent to finished, correctly textured models.
- Correct mesh-to-material binding, visual fidelity, all features, and native ROM testing remain incomplete.

## Repository policy
The decrypted commercial game image, copyrighted extracted model files, original textures, and large decoded collections are **not distributed in this repository**. Keep these local or in a user-controlled private asset store. The source scripts and compatible independently authored code can be version-controlled here.

See `docs/PROJECT_HANDOFF.md` and `docs/MODEL_RESTORATION_STATUS.md`.

## Next steps
1. Integrate the verified, independently authored restoration scripts and their tests.
2. Verify C62/C63 vertex and UV mapping against recovered local model binaries.
3. Recover original mesh/material assignments; visually compare model renders.
4. Integrate verified models into the DS renderer, compile with BlocksDS, and test in melonDS.

GitHub Actions checks do not themselves prove the project can boot on Nintendo DS hardware.

## Final-build asset policy
The original Pokédex 3D Pro game assets are **not required during ordinary source development, automated tests, or intermediate CI builds**. The user will supply their own extracted original assets **only at the final build stage**, after code, non-camera gameplay features, interface behavior, and asset-loading interfaces are completed and tested with synthetic fixtures.

The final build must **fail with a clear missing-assets message** if the required original assets are not supplied. It must not silently replace missing models or textures with inaccurate replicas. The original game dump and extracted proprietary assets must never be uploaded to GitHub or committed to source control. Native DS test builds may use neutral test assets; an asset-integrated final build is a separate last step. DSi camera AR is also reserved for the final feature milestone.

## Revised original-asset requirement (latest user instruction)
The goal is to finish porting **the actual game with its original assets**, not produce a generic lookalike. Original assets may be used during development, restoration, and test builds as needed to faithfully implement and verify the port. The previous final-build-only timing requirement is superseded. Keep the decrypted game image and proprietary asset payloads out of GitHub source control; use the user's private local assets during source builds and tests. Missing required originals must be reported explicitly, never substituted with inaccurate replicas.

## DS-Homebrew technical references

See [DS-Homebrew implementation references](docs/DS_HOMEBREW_REFERENCES.md) for TWiLight Menu++, nds-bootstrap, and GodMode9i patterns relevant to DS/DSi UI, storage, asset conversion and launch testing. The project remains a separate BlocksDS development ROM and does not bundle original Pokémon assets.
