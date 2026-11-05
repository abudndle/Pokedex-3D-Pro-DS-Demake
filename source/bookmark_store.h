#ifndef P3D_BOOKMARK_STORE_H
#define P3D_BOOKMARK_STORE_H
#include "bookmark_edit.h"
/* Independent dual-slot bookmark persistence. No original assets required. */
int p3dBookmarkStore(const char *base,const P3DBookmarkList *pokemon,const P3DBookmarkList *moves);
int p3dBookmarkLoad(const char *base,P3DBookmarkList *pokemon,P3DBookmarkList *moves);
#endif
