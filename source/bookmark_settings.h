#ifndef P3D_BOOKMARK_SETTINGS_H
#define P3D_BOOKMARK_SETTINGS_H
#include "bookmark_edit.h"
#include "feature_menu.h"
typedef struct {
 P3DBookmarkList pokemon,moves;
 uint8_t active_list; /* 0 Pokémon, 1 moves */
 uint8_t dirty;
} P3DBookmarkSettings;
void p3dBookmarkSettingsInit(P3DBookmarkSettings *s);
int p3dBookmarkSettingsSelectList(P3DBookmarkSettings *s,unsigned list);
void p3dBookmarkSettingsEdit(P3DBookmarkSettings *s,int enabled);
/* In Edit mode, tap removes bookmark. Otherwise opens its Dex selection.
 * Returns 1 for navigation, 2 for deletion, 0 for invalid/no-op. */
int p3dBookmarkSettingsSelect(P3DBookmarkSettings *s,P3DMenu *menu,unsigned slot);
#endif
