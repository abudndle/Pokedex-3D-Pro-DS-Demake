#ifndef P3D_MENU_LAYOUT_H
#define P3D_MENU_LAYOUT_H
#include <stddef.h>
#define P3D_MENU_VISIBLE_ROWS 6
#define P3D_MENU_LEFT 14
#define P3D_MENU_RIGHT 244
#define P3D_MENU_FIRST_Y 100
#define P3D_MENU_ROW_HEIGHT 11
size_t p3dMenuVisibleStart(size_t entry_count,int cursor);
int p3dMenuClampCursor(int cursor,size_t entry_count);
int p3dMenuHitTest(int x,int y,size_t entry_count,int cursor);
int p3dFeatureHitTest(int x,int y,size_t row_count);
int p3dAlbumPageTouch(int x,int y);
int p3dAlbumDeleteTouch(int x,int y);
#endif
