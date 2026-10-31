# Optional custom images in DS mode

Users may choose their own images in Settings when storage is accessible. Original game visuals remain the default and can always be restored.

## Implemented
- Asset-free selection state and filename validation for local `.bmp` images.
- Reject path traversal, unsupported file names, missing images, and unavailable storage.
- Safe fallback to original visuals.
- Host regression tests in GitHub Actions.

## Still to integrate
- Add a visible Settings screen picker and persistent preference field.
- Implement FAT/DLDI discovery for DS mode and SD access where supported on DSi.
- Decode supported images into a screen-compatible pixel buffer and display them as user-selected backgrounds only, not replacements for Pokémon mesh textures.
- Explain storage availability to users. An ordinary DS/DS Lite without a storage interface cannot browse files.
- Validate exact image dimensions, BMP pixel format and memory budget on hardware; unsupported files should not crash the app.

No original game files or user photos are uploaded to GitHub.
