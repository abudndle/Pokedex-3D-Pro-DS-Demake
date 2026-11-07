#include "game_save_bridge.h"
#include <assert.h>
#include <stdio.h>
#include <limits.h>
#include <string.h>
int main(void){
 P3DMenu menu;P3DSaveState save;int dex=-1,move=-1;
 p3dMenuReset(&menu);
 menu.rotate=0; menu.backdrop=2;
 assert(p3dFavoriteToggle(&menu,24)==1);
 assert(p3dFavoriteToggle(&menu,0)==1);
 assert(p3dGameSaveCapture(&save,&menu,24,12,3,10));
 p3dMenuReset(&menu);
 assert(p3dGameSaveRestore(&save,&menu,&dex,&move));
 assert(dex==24&&move==12&&p3dFavoriteContains(&menu,24)&&p3dFavoriteContains(&menu,0));
 assert(menu.rotate==0&&menu.backdrop==2);
 assert(!p3dGameSaveCapture(&save,&menu,-1,0,0,0));
 assert(!p3dGameSaveCapture(&save,&menu,649,0,0,0));
 assert(p3dGameSaveCapture(&save,&menu,648,0,0,0));
 save.selected_model=737; /* Legacy original-resource selection. */
 assert(p3dGameSaveRestore(&save,&menu,&dex,&move));
 assert(dex==648);
 save.favorite_count=2;
 save.favorites[0]=737;
 save.favorites[1]=24;
 assert(p3dGameSaveRestore(&save,&menu,&dex,&move));
 assert(menu.favorites_count==1&&menu.favorites[0]==24);
 assert(!p3dFavoriteContains(&menu,737));

 /* Capture must validate signed native IDs before narrowing to uint16_t.
  * 65536 formerly became species zero and produced a successful bad save. */
 const int invalid_ids[]={65536,-65536,-1,649,737,INT_MIN,INT_MAX};
 for(unsigned i=0;i<sizeof(invalid_ids)/sizeof(invalid_ids[0]);i++){
  p3dMenuReset(&menu);menu.favorites_count=1;menu.favorites[0]=invalid_ids[i];
  memset(&save,0xa5,sizeof(save));P3DSaveState before=save;
  assert(!p3dGameSaveCapture(&save,&menu,0,0,0,0));
  assert(!memcmp(&save,&before,sizeof(save)));
 }
 p3dMenuReset(&menu);menu.favorites_count=2;
 menu.favorites[0]=24;menu.favorites[1]=24;
 memset(&save,0xa5,sizeof(save));P3DSaveState before=save;
 assert(!p3dGameSaveCapture(&save,&menu,0,0,0,0));
 assert(!memcmp(&save,&before,sizeof(save)));
 /* Validation after constructing the record must also be atomic. */
 menu.favorites_count=1;menu.favorites[0]=648;
 assert(!p3dGameSaveCapture(&save,&menu,648,558,0,100000001));
 assert(!memcmp(&save,&before,sizeof(save)));
 assert(p3dGameSaveCapture(&save,&menu,648,558,10,10));
 assert(p3dGameSaveRestore(&save,&menu,&dex,&move));
 assert(dex==648&&move==558&&menu.favorites_count==1&&menu.favorites[0]==648);
 puts("Native gameplay save bridge: PASS");return 0;
}
