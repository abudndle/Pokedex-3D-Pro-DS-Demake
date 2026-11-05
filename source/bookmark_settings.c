#include "bookmark_settings.h"
#include "bookmark_navigation.h"
#include <string.h>
void p3dBookmarkSettingsInit(P3DBookmarkSettings *s){if(s)memset(s,0,sizeof(*s));}
int p3dBookmarkSettingsSelectList(P3DBookmarkSettings *s,unsigned list){
 if(!s||list>1)return 0;
 s->active_list=(uint8_t)list;
 p3dBookmarkSetEditing(&s->pokemon,0);
 p3dBookmarkSetEditing(&s->moves,0);
 return 1;
}
void p3dBookmarkSettingsEdit(P3DBookmarkSettings *s,int enabled){
 if(!s)return;
 p3dBookmarkSetEditing(&s->pokemon,s->active_list==0&&enabled);
 p3dBookmarkSetEditing(&s->moves,s->active_list==1&&enabled);
}
int p3dBookmarkSettingsSelect(P3DBookmarkSettings *s,P3DMenu *menu,unsigned slot){
 P3DBookmarkList *list;
 if(!s||s->active_list>1)return 0;
 list=s->active_list?&s->moves:&s->pokemon;
 if(list->editing){
  if(!p3dBookmarkEditTap(list,slot))return 0;
  s->dirty=1;return 2;
 }
 if(!menu||menu->page!=P3D_PAGE_SETTINGS)return 0;
 return s->active_list?p3dBookmarkOpenMove(menu,list,slot):
                       p3dBookmarkOpenPokemon(menu,list,slot);
}
