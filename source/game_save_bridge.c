#include "game_save_bridge.h"
#include <string.h>
int p3dGameSaveCapture(P3DSaveState *dst,const P3DMenu *menu,int dex_index,int move_index,int correct,int total){
 if(!dst||!menu||dex_index<0||dex_index>=P3D_SAVE_MODEL_LIMIT||
 move_index<0||move_index>=559||menu->favorites_count<0||
 menu->favorites_count>P3D_FAVORITES_MAX||menu->backdrop<0||menu->backdrop>3||menu->rotate<0||menu->rotate>1||correct<0||total<correct)return 0;
 memset(dst,0,sizeof(*dst));dst->selected_model=(uint16_t)dex_index;
 dst->move_index=(uint16_t)move_index;dst->favorite_count=(uint8_t)menu->favorites_count;
 for(int i=0;i<menu->favorites_count;i++)dst->favorites[i]=(uint16_t)menu->favorites[i];
 dst->backdrop=(uint8_t)menu->backdrop;dst->rotate=(uint8_t)menu->rotate;
 dst->challenge_correct=(uint32_t)correct;dst->challenge_total=(uint32_t)total;
 return p3dSaveStateValid(dst);
}
int p3dGameSaveRestore(const P3DSaveState *src,P3DMenu *menu,int *dex_index,int *move_index){
 if(!p3dSaveStateValid(src)||!menu||!dex_index||!move_index)return 0;
 p3dMenuReset(menu);
 menu->favorites_count=src->favorite_count;
 menu->backdrop=src->backdrop;menu->rotate=src->rotate;
 for(int i=0;i<src->favorite_count;i++)menu->favorites[i]=src->favorites[i];
 *dex_index=src->selected_model;*move_index=src->move_index;
 return 1;
}
