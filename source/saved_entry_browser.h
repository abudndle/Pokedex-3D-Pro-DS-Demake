#ifndef P3D_SAVED_ENTRY_BROWSER_H
#define P3D_SAVED_ENTRY_BROWSER_H
#include "feature_menu.h"
#include "records.h"
/* Text fallback only; zero-based libnds rows. Original artwork is gated by
 * the caller through controls_visible; no source-art hitboxes are inferred. */
#define P3D_SAVED_ENTRY_FIRST_ROW 11
#define P3D_SAVED_ENTRY_ROW_STEP 2
#define P3D_SAVED_RECENT_PAGE_SIZE 5
int p3dSavedEntryRow(unsigned visible_row);
/* Read-only hit tests return a saved-list index, never a species ID. */
int p3dFavoriteTouch(const P3DMenu *menu,int controls_visible,int x,int y);
int p3dRecentTouch(const P3DRecords *records,int cursor,int controls_visible,int x,int y);
#endif
