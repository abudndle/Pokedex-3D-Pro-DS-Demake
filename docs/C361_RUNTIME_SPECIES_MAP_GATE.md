# C361 model runtime reachability

The recovery pack can contain all730 structurally valid DS3M previews while
the game cannot display any: main resolves the canonical species through
`models/species_map.p3sm` before opening the preview. The available recovery
archive lacked that map. A file inventory was therefore not proof of rendering.

C137 now separately reports `runtime_species_preview_ready`, available species
slot count and specific missing/invalid/unavailable-reference issues. The
existing structural `native_preview_ready` flag retains its semantics. The
new `--require-runtime-preview-ready` exits unsuccessfully when the runtime map
cannot resolve any staged previews. A valid partial map reports its actual
coverage; it never implies all649 species or original identities are verified.

Synthetic regressions cover missing/truncated maps, reserved/unavailable
resources, entirely unmapped tables, valid partial tables and CLI exit status.
Existing archive safety and exact staging tests remain unchanged. No original
asset bytes, source names, private hashes or actual maps are bundled here.

Local authorized recovery validation also exercised the native C138 loader
against all730 actual previews, with exact XYZ/RGB emission checks. One limited
identity was corroborated using existing C88 evidence and recovered descriptor
names, enabling local model/zoom screenshots; the other648 canonical slots
remain unavailable. Full mapping, verified UV/material bindings, skeletal
animation semantics and hardware are unresolved. Private reports, images and
ROMs stay outside the public checkout and CI artifacts.
