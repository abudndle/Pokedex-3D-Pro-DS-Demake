#ifndef P3D_BOOKMARK_SESSION_H
#define P3D_BOOKMARK_SESSION_H
#include "bookmark_settings.h"
/* Restore persistent bookmarks at boot; missing/corrupt slots mean empty.
 * A successful deletion/addition can be flushed to the dual-slot store. */
int p3dBookmarkSessionLoad(P3DBookmarkSettings *settings,const char *base);
int p3dBookmarkSessionFlush(P3DBookmarkSettings *settings,const char *base);
int p3dBookmarkSessionAdd(P3DBookmarkSettings *settings,const char *base,
                          unsigned list,unsigned id);
int p3dBookmarkSessionSelect(P3DBookmarkSettings *settings,P3DMenu *menu,
                             const char *base,unsigned slot);
#endif
