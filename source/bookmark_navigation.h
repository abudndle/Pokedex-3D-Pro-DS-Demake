#ifndef P3D_BOOKMARK_NAVIGATION_H
#define P3D_BOOKMARK_NAVIGATION_H
#include "bookmark_edit.h"
#include "feature_menu.h"
/* Settings bookmark deep links: no mutation on invalid list/index/ID.
 * Pokémon ids are zero-based national species (0..648), not model ids. */
int p3dBookmarkOpenPokemon(P3DMenu *menu,const P3DBookmarkList *bookmarks,unsigned slot);
int p3dBookmarkOpenMove(P3DMenu *menu,const P3DBookmarkList *bookmarks,unsigned slot);
#endif
