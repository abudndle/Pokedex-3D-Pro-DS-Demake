#ifndef P3D_GAME_SAVE_BRIDGE_H
#define P3D_GAME_SAVE_BRIDGE_H
#include "feature_menu.h"
#include "save_store.h"
int p3dGameSaveCapture(P3DSaveState *dst,const P3DMenu *menu,int dex_index,int move_index,int correct,int total);
int p3dGameSaveRestore(const P3DSaveState *src,P3DMenu *menu,int *dex_index,int *move_index);
#endif
