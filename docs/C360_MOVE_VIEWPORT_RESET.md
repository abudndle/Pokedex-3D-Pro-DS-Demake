# C360 Move Dex text navigation

Touchscreen corner navigation previously changed the selected move without
resetting its description/effect scroll offset. A long description followed
by a short move could therefore appear empty and checkpoint a stale offset.
Keypad navigation already reset the viewport.

Both paths now share one bounded selection operation. A valid changed move
resets the offset to zero atomically; invalid targets, unchanged selections,
null and aliased outputs preserve state. Existing description/effect choice,
source-backed text, save formats and controls are preserved.

The behavioral regression was first run against the exact extracted old touch
assignment, failing the offset-zero assertion at runtime. The new helper and
existing C100 text tests pass. C260 adds an actual melonDS scenario: establish
a keypad short-text reference, scroll a synthetic long move, tap to the short
move, verify the same initial text and native FAT offset0, then restart.
Only owner-authored synthetic text is included in public fixtures/artifacts.

This repairs a DS navigation defect; original move data authenticity, full
3DS visual parity and hardware acceptance are separate unresolved requirements.
