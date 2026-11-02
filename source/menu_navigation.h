#ifndef P3D_MENU_NAVIGATION_H
#define P3D_MENU_NAVIGATION_H
int p3dMenuTouchIndex(int x,int y,int entry_count,int cursor);
int p3dMenuScroll(int cursor,int entry_count,int direction);
/* C218: browse the supported 649-entry Pokédex without overflow. */
int p3dDexNavigate(int current,int direction);
#endif
