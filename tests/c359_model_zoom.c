#include "model_view.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 P3DModelView v;p3dModelViewReset(&v);assert(p3dModelViewDistance(&v)==12);
 assert(p3dModelZoomTouch(&v,1,1,220,104));assert(p3dModelViewDistance(&v)==11);
 for(int i=0;i<50;i++)assert(p3dModelZoomTouch(&v,1,1,255,111));
 assert(p3dModelViewDistance(&v)==8);
 for(int i=0;i<50;i++)assert(p3dModelZoomTouch(&v,1,1,0,104));
 assert(p3dModelViewDistance(&v)==24);
 assert(p3dModelZoomTouch(&v,1,1,128,108));assert(p3dModelViewDistance(&v)==12);
 const int misses[][2]={{-1,104},{256,104},{128,103},{128,112},{128,88},{128,160}};
 for(unsigned i=0;i<sizeof(misses)/sizeof(misses[0]);i++){
  assert(!p3dModelZoomTouch(&v,1,1,misses[i][0],misses[i][1]));
  assert(p3dModelViewDistance(&v)==12);
 }
 assert(!p3dModelZoomTouch(&v,0,1,220,104));
 assert(!p3dModelZoomTouch(&v,1,0,220,104));
 assert(!p3dModelZoomTouch(NULL,1,1,220,104));
 assert(p3dModelViewDistance(NULL)==12);
 v.distance_quarters=-1;assert(p3dModelViewDistance(&v)==12);
 assert(p3dModelZoomTouch(&v,1,1,96,104));assert(v.distance_quarters==12);
 v.distance_quarters=100000;assert(p3dModelViewDistance(&v)==12);
 assert(p3dModelZoomTouch(&v,1,1,159,104));assert(v.distance_quarters==12);
 assert(p3dModelZoomTouch(&v,1,1,160,104));assert(v.distance_quarters==11);
 p3dModelViewReset(&v);assert(p3dModelViewDistance(&v)==12);
 puts("C359 bounded model zoom/reset, exact hit bounds and unavailable/art gating: PASS");return 0;
}
