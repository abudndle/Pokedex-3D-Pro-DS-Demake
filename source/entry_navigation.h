#ifndef P3D_ENTRY_NAVIGATION_H
#define P3D_ENTRY_NAVIGATION_H
#include "feature_menu.h"
/* Explicit entry opening consumes the initiating buttons and clears local
 * presentation state even when reopening the current entry. Outputs must be
 * separate objects outside the menu. Invalid requests leave all state intact. */
int p3dEntryOpenPokemon(P3DMenu *menu,int target,int *dex,int *form,
                        int *detail_tab,unsigned *buttons);
int p3dEntryOpenMove(P3DMenu *menu,int target,int *move,int *text_offset,
                     int *effect,unsigned *buttons);
#endif
