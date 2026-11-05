#include "bookmark_navigation.h"
#define NATIONAL_SPECIES_COUNT 649
#define MOVE_DEX_COUNT 559
int p3dBookmarkOpenPokemon(P3DMenu *menu,const P3DBookmarkList *bookmarks,unsigned slot){
 if(!menu||!p3dBookmarkValid(bookmarks,NATIONAL_SPECIES_COUNT)||slot>=bookmarks->count)return 0;
 menu->page=P3D_PAGE_DEX;
 menu->selected_dex=bookmarks->ids[slot];
 menu->cursor=bookmarks->ids[slot];
 return 1;
}
int p3dBookmarkOpenMove(P3DMenu *menu,const P3DBookmarkList *bookmarks,unsigned slot){
 if(!menu||!p3dBookmarkValid(bookmarks,MOVE_DEX_COUNT)||slot>=bookmarks->count)return 0;
 menu->page=P3D_PAGE_MOVES;
 menu->move_index=bookmarks->ids[slot];
 menu->cursor=bookmarks->ids[slot];
 menu->move_effect=0;
 menu->move_page=0;
 return 1;
}
