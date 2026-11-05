#include "bookmark_settings.h"
#include <assert.h>
int main(void){
 P3DBookmarkSettings s;P3DMenu menu;
 p3dBookmarkSettingsInit(&s);p3dMenuReset(&menu);menu.page=P3D_PAGE_SETTINGS;
 assert(p3dBookmarkAdd(&s.pokemon,25,649));
 assert(p3dBookmarkAdd(&s.moves,50,559));
 assert(p3dBookmarkSettingsSelect(&s,&menu,0)==1);
 assert(menu.page==P3D_PAGE_DEX&&menu.selected_dex==25);
 menu.page=P3D_PAGE_SETTINGS;
 assert(p3dBookmarkSettingsSelectList(&s,1));
 assert(p3dBookmarkSettingsSelect(&s,&menu,0)==1);
 assert(menu.page==P3D_PAGE_MOVES&&menu.move_index==50);
 menu.page=P3D_PAGE_SETTINGS;
 p3dBookmarkSettingsEdit(&s,1);
 assert(!p3dBookmarkSettingsSelect(&s,&menu,2));
 assert(p3dBookmarkSettingsSelect(&s,&menu,0)==2);
 assert(s.dirty&&s.moves.count==0&&s.pokemon.count==1);
 assert(menu.page==P3D_PAGE_SETTINGS);
 assert(p3dBookmarkSettingsSelectList(&s,0));
 assert(!s.pokemon.editing&&!s.moves.editing);
 p3dBookmarkSettingsEdit(&s,1);
 assert(p3dBookmarkSettingsSelect(&s,&menu,0)==2);
 assert(s.pokemon.count==0);
 assert(!p3dBookmarkSettingsSelectList(&s,2));
 return 0;
}
