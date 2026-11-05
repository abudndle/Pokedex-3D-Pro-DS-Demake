#include "bookmark_session.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DBookmarkSettings a,b;P3DMenu menu;char path[256];
 assert(argc==2);
 assert(!p3dBookmarkSessionLoad(&a,argv[1]));
 assert(p3dBookmarkSessionAdd(&a,argv[1],0,100));
 assert(p3dBookmarkSessionAdd(&a,argv[1],1,200));
 assert(!a.dirty);
 assert(p3dBookmarkSessionLoad(&b,argv[1]));
 assert(b.pokemon.count==1&&b.pokemon.ids[0]==100);
 assert(b.moves.count==1&&b.moves.ids[0]==200);
 p3dMenuReset(&menu);menu.page=P3D_PAGE_SETTINGS;
 assert(p3dBookmarkSessionSelect(&b,&menu,argv[1],0)==1);
 assert(menu.page==P3D_PAGE_DEX&&menu.selected_dex==100);
 menu.page=P3D_PAGE_SETTINGS;
 p3dBookmarkSettingsEdit(&b,1);
 assert(p3dBookmarkSessionSelect(&b,&menu,argv[1],0)==2);
 assert(!b.dirty&&b.pokemon.count==0);
 assert(p3dBookmarkSessionLoad(&a,argv[1]));
 assert(a.pokemon.count==0&&a.moves.count==1);
 assert(!p3dBookmarkSessionAdd(&a,argv[1],0,649));
 assert(snprintf(path,sizeof(path),"%s_bookmarks_A.sav",argv[1])<(int)sizeof(path));
 remove(path);
 assert(snprintf(path,sizeof(path),"%s_bookmarks_B.sav",argv[1])<(int)sizeof(path));
 remove(path);
 return 0;
}
