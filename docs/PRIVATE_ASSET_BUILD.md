# Private original-assets integration

The port must use the user's privately held original Pokédex 3D Pro assets for accurate rendering. Proprietary game data is not stored in this repository or GitHub Actions.

## Build boundary

The native BlocksDS project mounts a private NitroFS directory at build time. The asset manifest is a JSON file with `format: "p3d-ds-original-assets-v1"` and a nonempty `assets` list. Every entry has `path`, `size`, and `sha256` fields.

Example (fake test fixture, **not** a commercial game asset):

```json
{
  "format": "p3d-ds-original-assets-v1",
  "assets": [{
    "path": "pokemon/test.dat",
    "size": 4,
    "sha256": "61c00a8e9cb3420d8c423ec79c7e4607b72904b12d12e6ca08a0c89b78510f2"
  }]
}
```

Run `python3 tools/validate_original_assets.py --manifest /private/manifest.json --root /private/nitrofs` before an original-asset build. The script checks required paths, size, SHA-256, and path traversal. It never downloads, creates, or uploads original assets.

The manifest is intentionally not prepopulated with invented original filenames or hashes. Those must be collected from the genuine verified extracted assets. This tool validates presence and integrity; it does **not** yet confirm texture-to-model mapping or visual fidelity.

## Required future integration

- Restore the full C14 port source and its model loader.
- Define a complete, evidence-based manifest based on the extracted originals.
- Wire this validator into the BlocksDS asset-integrated build target.
- Validate model appearances in melonDS and on hardware where available.
