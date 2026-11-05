#include "bookmark_navigation.h"
#include <assert.h>
#include <string.h>
int main(void){
 P3DMenu menu;P3DMenu before;
 P3DBookmarkList pokemon={0},moves={0};
 memset(&menu,0,sizeof(menu));menu.page=P3D_PAGE_SETTINGS;menu.cursor=8;
 assert(p3dBookmarkAdd(&pokemon,648,649));
 assert(p3dBookmarkAdd(&moves,558,559));
 assert(p3dBookmarkOpenPokemon(&menu,&pokemon,0));
 assert(menu.page==P3D_PAGE_DEX&&menu.selected_dex==648&&menu.cursor==648);
 menu.page=P3D_PAGE_SETTINGS;menu.move_effect=1;menu.move_page=5;
 assert(p3dBookmarkOpenMove(&menu,&moves,0));
 assert(menu.page==P3D_PAGE_MOVES&&menu.move_index==558&&menu.cursor==558);
 assert(menu.move_effect==0&&menu.move_page==0);
 before=menu;assert(!p3dBookmarkOpenMove(&menu,&moves,1));
 assert(!memcmp(&before,&menu,sizeof(menu)));
 moves.ids[0]=559;assert(!p3dBookmarkOpenMove(&menu,&moves,0));
 assert(!memcmp(&before,&menu,sizeof(menu)));
 assert(!p3dBookmarkOpenPokemon(0,&pokemon,0));
 assert(!p3dBookmarkOpenPokemon(&menu,0,0));
 return 0;
}
