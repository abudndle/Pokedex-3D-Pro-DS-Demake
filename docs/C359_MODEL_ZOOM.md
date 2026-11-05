# C359 native model zoom/reset

Adds a DS touchscreen adaptation to the actual 3D model view: zoom out, reset
and zoom in on native text row14. The camera distance uses integer quarter
units, default12 (3 units), bounded8..24 (2..6 units). Rendering uses the
existing DS fixed-point translation. Species/form reload and restart restore
the default view; save formats are unchanged.

Controls are available only for a loaded preview on the plain Pokédex entry.
Source-art overlays, title/idle, HOME, details and missing meshes do not expose
these hitboxes. Existing shoulder rotation, animation selection/playback,
favorites, form selection and entry navigation are preserved. Exact original
3DS camera limits/controls and physical DS/DSi behavior are not verified.

`run_c359_model_zoom.sh` compiled against inert API scaffolding and failed the
first zoom-touch assertion before behavior was implemented. The same command
passes after implementation, including exact hit bounds, clamping, reset,
unavailable/art gating and invalid-state recovery. The C306 workflow uses
independently authored red geometry and real DeSmuME touchscreen input to
check enlargement, reduction and exact reset; negative frame fixtures reject
missing, blank and incorrect rendered-size evidence.

Authorized private development builds and captures are kept outside this
checkout and never uploaded to public CI. The existing recovery pack has
730 structurally compatible previews but no full canonical species map,
verified UV/material binding or original skeletal animation integration.
One limited source identity has been independently corroborated for local
render testing; this is not a complete 649-species/730-form integration.
Original visual fidelity, complete mapping and hardware remain unfinished.
