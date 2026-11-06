#include "move_text_view.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
/* Defect: touch navigation retained the preceding move's scroll position,
 * hiding short original text and checkpointing an unrelated offset. */
int main(void){
 char long_text[281];memset(long_text,'L',280);long_text[280]=0;
 int index=0,offset=p3dMoveTextScroll(168,long_text,1);
 assert(offset==196);
 assert(p3dMoveNavigateSelect(&index,&offset,1)==1);
 assert(index==1);assert(offset==0);
 assert(p3dMoveTextScroll(offset,"Short original description",0)==0);
 offset=28;
 assert(!p3dMoveNavigateSelect(&index,&offset,1));assert(index==1&&offset==28);
 assert(!p3dMoveNavigateSelect(&index,&offset,-1));assert(index==1&&offset==28);
 assert(!p3dMoveNavigateSelect(&index,&offset,559));assert(index==1&&offset==28);
 assert(!p3dMoveNavigateSelect(NULL,&offset,2));assert(offset==28);
 assert(!p3dMoveNavigateSelect(&index,NULL,2));assert(index==1);
 assert(!p3dMoveNavigateSelect(&index,&index,2));assert(index==1);
 assert(p3dMoveNavigateSelect(&index,&offset,558));assert(index==558&&offset==0);
 offset=56;
 assert(!p3dMoveNavigateSelect(&index,&offset,558));assert(offset==56);
 assert(p3dMoveNavigateSelect(&index,&offset,0));assert(index==0&&offset==0);
 puts("C360 move selection resets text viewport atomically: PASS");return 0;
}
