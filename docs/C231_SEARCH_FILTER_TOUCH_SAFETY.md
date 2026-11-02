# C231 — Filtered Search safety and text-mode touch alignment

## Native Pokédex behavior

The DS Search page previously kept a numeric selection when its typed query, source-text field, region or ALL/VIEWED/FAVORITES scope changed. If no original text result matched, pressing **A** could open that unrelated Pokémon and **Y** could favorite it. C231 validates the selected record against the **current** original P3DX text and scope every time either action is offered. Filter/query edits try to move to the next matching original record; if none exists, the numeric cursor is retained for later browsing but displays **No matching original entry** and cannot be opened or favorited.

Removing the last favorite that matches a Favorites-filtered search immediately refreshes this state. Empty unfiltered numeric browsing still works when privately staged original text is unavailable. No fabricated names, descriptions, or 3DS GUI graphics are used.

The native fallback console and touch mapper now share one-based text row constants. Both filters are displayed side-by-side on row **12** (touch y=88–103), the field is on row **14** (y=104–119), result on row **16** (not touch actionable), the two 13-letter keyboard rows are **19** and **21** (y=144–175), and Delete/Next/Previous are on row **23** (y=176–191). The guidance line occupies separate row **24**. The original bitmap artwork does not acquire speculative touch hitboxes.

During a touchscreen press on the Search page, A/Y/navigation input cannot cause a second action. Switching from Search to another feature consumes the same-frame keys, preserving existing Dex, Move Dex, Settings, Favorites and resume controls without accidental downstream toggles.

## Tests and boundaries

- Run: sh tests/run_c82_dex_search.sh; this exercises the real C source-text reader with 649 synthetic P3DX records, stale/no-match selections, name/description and regional scope, favorite removal, unavailable original text, and invalid arguments.
- Run: sh tests/run_c83_search_touch.sh; this tests all 26 letters against rendered console row locations, region/scope/field strips, action regions and edges of the 256×192 touchscreen.
- make check-host includes both portable regressions.
- The public GitHub port-source workflow runs both regressions and the native BlocksDS workflows compile and validate an asset-free ROM; emulator startup checks do not prove all touch paths or original-art parity.

Original art, C5 models, real P3DX files, private decrypted game archives, ROMs and private per-model manifests are not part of this source change. The unfinished source UI artwork mapping, multilingual text, true original Challenge gameplay and original-asset visual comparisons remain separate release gates.
