# Filtered Search selection and text-screen alignment

Search previously retained its numeric cursor after an unmatched prefix or
filter change. The stale entry remained available to A and Y. The native UI now
checks the displayed selection against the current name/description query,
region, and ALL/VIEWED/FAVORITES scope before opening or favoriting it. Query
and filter edits refresh to a valid result when one exists. A failed search
keeps the numeric cursor but displays **No matching original entry** and blocks
actions on that cursor. Removing the last matching favorite immediately leaves
the same safe no-match state.

Numeric browsing without active filters remains usable when the private text
catalog is missing. No original species names or descriptions are fabricated.
Touch input that edits a query cannot also open or favorite a result in the
same frame. Search navigation to Dex, Favorites, Settings or Move Dex is not
processed again by the destination page, preventing accidental favorite toggles
and unwanted second navigation.

The source text UI now shares one-based console row constants with the C83
touch mapper: region/scope row 12, field row 14, result row 16, keyboard rows
19/21 and action row 23. These correspond to the existing touchscreen targets
at y=88/104/144/160/176. The B hint stays outside those targets. No new hitboxes
are assigned to original bitmap artwork.

Host regressions cover stale/no-match selections, description and region
filters, viewed/favorite restrictions, favorite removal, absent text, invalid
arguments, and every rendered keyboard key and boundary. The existing host
suite also required direct test includes, a corrected invalid-scope test call,
real PNG signature/row bytes in malformed-image fixtures, and a native source
evidence link in the feature-parity inventory. Assertions and the incomplete
game release gate remain enabled.

The user's split CCI was independently reassembled and its main RomFS inventory
extracted into private storage outside this checkout. This supplied 5,564 files,
including 730 original model containers. Original payloads, manifests containing
their paths/hashes, decoded research outputs and the assembled CCI are not part
of this PR. Extracting files does not establish correct conversion of compressed
model/text/GUI resources or visual parity on Nintendo DS/DSi.
