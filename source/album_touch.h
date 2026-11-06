#ifndef P3D_ALBUM_TOUCH_H
#define P3D_ALBUM_TOUCH_H
#include <stddef.h>
enum {P3D_ALBUM_TOUCH_NONE, P3D_ALBUM_TOUCH_SELECT, P3D_ALBUM_TOUCH_OPEN,
      P3D_ALBUM_TOUCH_PREV, P3D_ALBUM_TOUCH_NEXT, P3D_ALBUM_TOUCH_PLAY,
      P3D_ALBUM_TOUCH_LIST};
#define P3D_ALBUM_LIST_ROW 13
#define P3D_ALBUM_NAV_ROW 22
#define P3D_ALBUM_ACTION_ROW 23
#define P3D_ALBUM_PLAY_ROW 18
#define P3D_ALBUM_RETURN_ROW 20
int p3dAlbumListTouch(size_t shown,size_t selected,int visible,int x,int y,size_t *next);
int p3dAlbumViewerTouch(int visible,int x,int y);
#endif
