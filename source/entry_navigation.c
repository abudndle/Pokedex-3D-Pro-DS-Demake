#include "entry_navigation.h"
#include <stdint.h>
/* Validate before changing any destination. Integer address differences avoid
 * ordering unrelated C pointers and avoid overflowing an end address. */
static int overlaps(const void *a,size_t a_size,const void *b,size_t b_size){
 uintptr_t aa=(uintptr_t)a,bb=(uintptr_t)b;
 return aa<=bb?bb-aa<a_size:aa-bb<b_size;
}
static int valid_outputs(P3DMenu *menu,int *first,int *second,int *third,unsigned *buttons){
 const void *outputs[4]={first,second,third,buttons};
 const size_t sizes[4]={sizeof(*first),sizeof(*second),sizeof(*third),sizeof(*buttons)};
 if(!menu||menu->page<0||menu->page>=P3D_PAGE_COUNT)return 0;
 for(int i=0;i<4;i++){
  if(!outputs[i]||overlaps(menu,sizeof(*menu),outputs[i],sizes[i]))return 0;
  for(int j=0;j<i;j++)if(overlaps(outputs[i],sizes[i],outputs[j],sizes[j]))return 0;
 }
 return 1;
}
int p3dEntryOpenPokemon(P3DMenu *menu,int target,int *dex,int *form,
                        int *detail_tab,unsigned *buttons){
 if(target<0||target>=649||!valid_outputs(menu,dex,form,detail_tab,buttons))return 0;
 menu->page=P3D_PAGE_DEX;menu->selected_dex=target;
 *dex=target;*form=0;*detail_tab=0;*buttons=0;
 return 1;
}
int p3dEntryOpenMove(P3DMenu *menu,int target,int *move,int *text_offset,
                     int *effect,unsigned *buttons){
 if(target<0||target>=559||!valid_outputs(menu,move,text_offset,effect,buttons))return 0;
 menu->page=P3D_PAGE_MOVES;menu->move_index=target;
 menu->move_effect=0;menu->move_page=0;
 *move=target;*text_offset=0;*effect=0;*buttons=0;
 return 1;
}
