#include "model_animation.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DAnimationClip a={0};
 assert(argc==5);
 assert(p3dAnimationFrameAt(&a,0)==-1);
 assert(p3dAnimationLoad(&a,argv[1]));
 assert(a.count==2&&a.total_ticks==5);
 assert(p3dAnimationFrameAt(&a,0)==0);
 assert(p3dAnimationFrameAt(&a,1)==0);
 assert(p3dAnimationFrameAt(&a,2)==1);
 assert(p3dAnimationFrameAt(&a,4)==1);
 assert(p3dAnimationFrameAt(&a,5)==0);
 assert(!p3dAnimationLoad(&a,argv[2]));
 assert(p3dAnimationFrameAt(&a,0)==-1);
 assert(!p3dAnimationLoad(&a,argv[3])); /* truncated frame */
 assert(!p3dAnimationLoad(&a,argv[4])); /* trailing bytes */
 assert(p3dAnimationFrameAt(&a,0)==-1);
 puts("Animation clip transport: PASS");
 return 0;
}
