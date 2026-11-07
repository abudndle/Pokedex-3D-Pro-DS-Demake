#include "game_save_bridge.h"
#include <string.h>
#define P3D_NATIVE_DEX_ENTRIES 649
int p3dGameSaveCapture(P3DSaveState *dst,const P3DMenu *menu,int dex_index,int move_index,int correct,int total){
 P3DSaveState candidate;
 if(!dst||!menu||dex_index<0||dex_index>=P3D_NATIVE_DEX_ENTRIES||
 move_index<0||move_index>=559||menu->favorites_count<0||
 menu->favorites_count>P3D_FAVORITES_MAX||menu->backdrop<0||menu->backdrop>3||menu->rotate<0||menu->rotate>1||correct<0||total<correct)return 0;
 /* Native favorite IDs must be checked before narrowing; legacy resource
  * IDs remain supported only by the existing restore migration below. */
 for(int i=0;i<menu->favorites_count;i++)
  if(menu->favorites[i]<0||menu->favorites[i]>=P3D_NATIVE_DEX_ENTRIES)return 0;
 memset(&candidate,0,sizeof(candidate));candidate.selected_model=(uint16_t)dex_index;
 candidate.move_index=(uint16_t)move_index;candidate.favorite_count=(uint8_t)menu->favorites_count;
 for(int i=0;i<menu->favorites_count;i++)candidate.favorites[i]=(uint16_t)menu->favorites[i];
 candidate.backdrop=(uint8_t)menu->backdrop;candidate.rotate=(uint8_t)menu->rotate;
 candidate.challenge_correct=(uint32_t)correct;candidate.challenge_total=(uint32_t)total;
 if(!p3dSaveStateValid(&candidate))return 0;
 *dst=candidate;return 1;
}
int p3dGameSaveRestore(const P3DSaveState *src,P3DMenu *menu,int *dex_index,int *move_index){
 if(!p3dSaveStateValid(src)||!menu||!dex_index||!move_index)return 0;
 p3dMenuReset(menu);
 menu->backdrop=src->backdrop;menu->rotate=src->rotate;
 /* Some legacy saves contain resource IDs outside the 649-entry native Dex.
    Omit only those entries; do not allow an unreachable favorite to open. */
 for(int i=0;i<src->favorite_count;i++)
  if(src->favorites[i]<P3D_NATIVE_DEX_ENTRIES)
   menu->favorites[menu->favorites_count++]=src->favorites[i];
 /* Older save files may carry a larger original-resource index. Keep the
    record usable while clamping its selection to the native 649-entry Dex. */
 *dex_index=src->selected_model<P3D_NATIVE_DEX_ENTRIES?src->selected_model:P3D_NATIVE_DEX_ENTRIES-1;
 *move_index=src->move_index;
 return 1;
}
