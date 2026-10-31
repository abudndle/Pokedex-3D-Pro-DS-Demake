# Project handoff

## Identity
Pokédex 3D Pro demake for DS, DS Lite, and DSi. Separate from the user's Pokémon Dream Radar DS project.

## Requirements
- Original-style Pokédex UI, backgrounds, Pokémon models, animations, and functionality.
- The user does not want substitute replica Pokémon models.
- All non-camera features must work on DS and DSi hardware.
- DSi-only camera AR should be developed last and hidden on DS/DS Lite.
- For DSi photos, use a separate Pokédex 3D Pro album folder on the system SD card.
- Preserve original asset backups and never claim placeholder renderings are final.

## Latest recovery stages
- C39: located original indexed model binaries in user's decrypted game image.
- C56: decoded 730 C5 model containers. Seven contain nonstandard descriptor flag 0x26, warranting special interpretation.
- C58: ten vertex-layout families identified.
- C62: 528 UV-equipped OBJ exports from whole-model matches.
- C63: 162 additional partially UV-equipped OBJ exports from mesh-level matches.
- Current work: material bindings, remaining UVs, Bulbasaur visual fidelity, renderer and emulator verification.

## Limitations
The 730 model files are indexed model entries rather than 730 independently identified Pokémon species. Recovery counts do not imply final artwork, material mapping, or emulator compatibility.

## Repository setup
Keep source code, scripts, manifests without copyrighted payload data, documentation and GitHub Actions here. Original model data and game dumps must be handled separately.
