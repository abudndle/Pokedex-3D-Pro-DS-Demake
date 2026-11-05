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
 /* A failed FAT write must retain the dirty in-memory change for retry. */
 {
  P3DBookmarkSettings pending,recovered;
  char invalid_base[256];
  assert(snprintf(invalid_base,sizeof(invalid_base),"%s/missing-parent/bookmarks",argv[1])<(int)sizeof(invalid_base));
  p3dBookmarkSettingsInit(&pending);
  assert(!p3dBookmarkSessionAdd(&pending,invalid_base,0,123));
  assert(pending.dirty&&pending.pokemon.count==1&&pending.pokemon.ids[0]==123);
  assert(p3dBookmarkSessionFlush(&pending,argv[1]));
  assert(!pending.dirty);
  assert(p3dBookmarkSessionLoad(&recovered,argv[1]));
  assert(recovered.pokemon.count==1&&recovered.pokemon.ids[0]==123);
  assert(recovered.moves.count==0);
 }
 assert(snprintf(path,sizeof(path),"%s_bookmarks_A.sav",argv[1])<(int)sizeof(path));
 remove(path);
 assert(snprintf(path,sizeof(path),"%s_bookmarks_B.sav",argv[1])<(int)sizeof(path));
 remove(path);
 return 0;
}
