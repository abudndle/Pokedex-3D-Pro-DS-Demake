# C240 — DeSmuME 0.9.13 CLI input ABI regression (asset-free CI only)

## Root cause, independently confirmed from the 0.9.13 source

The installed Ubuntu DeSmuME CLI is `0.9.13-4build1`. Its
`src/frontend/posix/cli/main.cpp` calls
`desmume_config_read_file(cli_kb_cfg)` and then *unconditionally* calls
`load_default_config(cli_kb_cfg)` again, discarding the parsed `[KEYS]`
settings. The 0.9.13 `ctrlssdl.cpp` declares `keyboard_cfg` as an array
of **16-bit** integers, but `main.cpp` declares `cli_kb_cfg` as **32-bit**
integers. `load_default_config` copies `sizeof(keyboard_cfg)` bytes
straight from the 32-bit defaults. On the little-endian CI host, this
interleaves the low/high halves of the defaults rather than copying
15 independent key codes.

In particular, the DS B slot (index 1) contains 0 (high half of x), and
the DS Right slot (index 4) contains 229 (low half of SDL2 RShift).
Consequently the normal `z`/Right keys cannot be used as B/Right,
even though SDL2 receives the events and the GLib config file is read.
This also explains the earlier `z` → Select and Right → R-shoulder
diagnostic masks. The 0.9.13 configuration group is `[KEYS]`; newer
upstream master uses `[SDLKEYS]`, but changing this alone cannot
work around the unconditional default reset.

Source references (upstream open-source DeSmuME, **not** Nintendo data):
- https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/frontend/posix/cli/main.cpp
- https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/frontend/posix/shared/ctrlssdl.cpp
- https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/frontend/posix/shared/desmume_config.cpp

## Bounded workaround and acceptance

The draft-only `tests/c238_sdl_event_trace.c` LD_PRELOAD adapter
observes real SDL2 keyboard events and GLib key reads. Only with
`P3D_C240_ADAPT_0913=1`, and only for the 0.9.13 CI binary, it
changes **SDL event keycodes**, not Nintendo DS RAM, framebuffer, or
game logic: injected `d` (100) becomes 229 (DS Right) and injected
`b` (98) becomes 0 (DS B). Keydown and keyup are both translated.
All other events are passed through unchanged. The CI job checks the
installed package version before enabling this workaround.

A synthetic host test verifies both translations and disabled
pass-through. Native BlocksDS compilation, ROM/header validation, and
the strict *real DeSmuME* four-frame #001→#002→HOME gate must all
pass before merging the draft PR. A visible frame transition in an
**asset-free** development ROM is not evidence of original 3DS model,
texture, animation, audio, or DSi AR fidelity. Keep original game
assets and converted geometry out of public GitHub and CI artifacts.
