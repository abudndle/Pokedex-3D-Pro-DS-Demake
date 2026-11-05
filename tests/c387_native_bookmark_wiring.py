#!/usr/bin/env python3
"""Native DS bookmark wiring guard; complements the C unit and BlocksDS build."""
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "source/main.c").read_text()
checks = {
    "bookmark module linked": '#include "bookmark_session.h"',
    "bookmark initialized": "p3dBookmarkSettingsInit(&bookmark_settings);",
    "bookmark loaded from FAT": "p3dBookmarkSessionLoad(&bookmark_settings,P3D_SAVE_BASE)",
    "bookmark saved": "p3dBookmarkSessionAdd(&bookmark_settings,",
    "bookmark selected": "p3dBookmarkSessionSelect(&bookmark_settings,&state,",
    "bookmark edit toggled": "p3dBookmarkSettingsEdit(&bookmark_settings,!editing);",
    "global SELECT excluded from Settings": "(home || state.page!=P3D_PAGE_SETTINGS)",
    "slot clamped after deletion": "if(bookmark_cursor>=count)bookmark_cursor=count?count-1:0;",
}
for label, needle in checks.items():
    if needle not in source:
        raise SystemExit(f"Missing native bookmark invariant: {label}")
if "if((down&KEY_START)&&progress_dirty && (home || state.page!=P3D_PAGE_SETTINGS))" not in source:
    raise SystemExit("Global START must not intercept Settings bookmark saves")
print(f"Native bookmark wiring: {len(checks)+1} invariants verified")
