#include "model_animation.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DAnimationClip a={0};
 P3DAnimationFrame pose={0};
 assert(argc==6);
 assert(!p3dAnimationPoseAt(&a,0,&pose));
 assert(!p3dAnimationPoseAt(&a,0,NULL));
 assert(p3dAnimationFrameAt(&a,0)==-1);
 assert(p3dAnimationLoad(&a,argv[1]));
 assert(a.count==2&&a.total_ticks==5&&a.version==1);
 assert(p3dAnimationPoseAt(&a,1,&pose));
 assert(pose.yaw==0 && pose.duration==2);
 assert(p3dAnimationPoseAt(&a,4,&pose));
 assert(pose.yaw==64 && pose.duration==3);
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
 assert(p3dAnimationLoad(&a,argv[5]));
 assert(a.count==2 && a.version==2 && a.total_ticks==8);
 assert(p3dAnimationPoseAt(&a,0,&pose) && pose.yaw==32760);
 assert(p3dAnimationPoseAt(&a,1,&pose) && pose.yaw==32764);
 assert(p3dAnimationPoseAt(&a,2,&pose) && pose.yaw==0);
 assert(pose.pitch==16384 && pose.roll==32);
 assert(p3dAnimationPoseAt(&a,3,&pose) && pose.yaw==4);
 assert(p3dAnimationPoseAt(&a,4,&pose) && pose.yaw==8);
 assert(p3dAnimationPoseAt(&a,6,&pose) && pose.yaw==0);
 assert(p3dAnimationPoseAt(&a,7,&pose) && pose.yaw==32764);
 assert(p3dAnimationPoseAt(&a,8,&pose) && pose.yaw==32760);
 assert(!p3dAnimationPoseAt(NULL,0,&pose));
 assert(!p3dAnimationPoseAt(&a,0,NULL));
 a.ready=0;
 assert(!p3dAnimationPoseAt(&a,0,&pose));
 puts("Animation clip transport and smooth playback: PASS");
 return 0;
}
