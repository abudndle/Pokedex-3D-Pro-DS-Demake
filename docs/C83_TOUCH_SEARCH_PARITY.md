# C83 — Touchscreen original-data search

This is a functional DS text-navigation implementation, not a redesign of original Pokédex 3D Pro artwork.

## Controls

In the Search page, press SELECT to switch to text-navigation mode when an original bitmap overlay is active. Touch 13 letters on each of two rows (A–M and N–Z) to enter an uppercase query of at most 12 letters. Tap top-left filter strip (y=88–103) to cycle National/Kanto/Johto/Hoenn/Sinnoh/Unova; top-right strip to cycle ALL/VIEWED/FAVORITES. Tap the next strip (y=104–119) to toggle NAME vs DESCRIPTION. Tap the lower strip (y=176–191) to delete, search next, or search previous.

The search results use *only* verified private original-English `data/dex_en.p3dx` records. Missing original data yields no match rather than invented results. Numeric arrow navigation, A to open Dex, L to Move Dex, R to Settings, Y to favorite, and plain X to Favorites remain available. Keyboard actions do not conflict with existing number-based lower-corner taps; generic touch navigation is skipped on Search page.

## Safety and tests

All touch coordinates are bounded to the DS 256x192 touchscreen. There are no guessed touch hitboxes on original UI artwork. The new `search_touch.c` module has a synthetic portable C regression covering 26 letters, margins, boundaries and all actions; normal native BlocksDS smoke CI compiles it.

The original art's exact keyboard, multilingual name/description search, touch scrolling, voice entry, complete in-game source appearance and all 36 original Challenge modes are still unfinished.
