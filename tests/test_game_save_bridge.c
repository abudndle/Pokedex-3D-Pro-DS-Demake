#include "game_save_bridge.h"
#include <assert.h>
#include <stdio.h>
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
 puts("Native gameplay save bridge: PASS");return 0;
}
