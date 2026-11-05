# C398 preserve rendered information

The shared row17 Back hint overwrote page-owned content: the middle Move Dex
text line, type effectiveness, form names, record rows and bookmark labels.
It also hid the learnset page-control hint. This was visible in actual private
ROM captures, not just a source-layout concern.

The generic footer now uses the free final console row on applicable pages.
Dex, Search and Album retain their own bottom-row controls. Dex entry's existing
START hint also names B; details retain START/B controls. No touch targets,
gameplay values or save formats change.

Records also placed its seven supported quiz scores on rows13,15,...25,
overwriting the control row and placing the final mode off-screen. Its score
rows now use13..19, preserving all seven values and the navigation/footer rows.
The regression first failed with the old spacing and now checks every supported
mode stays visible, ordered and outside the control/footer area.

The portable footer policy regression checks against the pages' occupied data
and control rows. The old row17 policy compiled and failed the non-overlap
assertion before the production change; the same command passes afterward.
The integrated host/build/emulator suite and fresh private source-bound
screenshots must verify the final revision.

BlocksDS console positions are zero-based and clamp to row 23. Page-specific free rows preserve existing controls, including Settings storage feedback. Zoom label and touch band occupy pixels 112 through 119. Album navigation uses free row 22; Search keeps its action labels instead of overwriting them with a hint.
