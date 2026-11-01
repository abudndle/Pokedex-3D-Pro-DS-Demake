/* C151 original source animation owner/node binding; synthetic rig only. */
#include <stdio.h>
#include <string.h>
#include "original_track_binding.h"
static P3DOriginalSkeleton rig;
static int check(const char *path){
    if(!p3dOriginalSkeletonLoad(&rig,path,14))return 1;
    P3DOriginalTrackOwner owners[2]={{0,"Base"},{1,"BoneRoot"}};
    uint16_t resolved[2]={123,456};
    if(!p3dOriginalTrackBind(&rig,owners,2,resolved)||
       resolved[0]!=0||resolved[1]!=1)return 2;
    if(!p3dOriginalTrackBind(&rig,NULL,0,NULL))return 3;
    owners[1].source_node_index=0;
    if(p3dOriginalTrackBind(&rig,owners,2,resolved)||
       resolved[0]!=0xffffu||resolved[1]!=0xffffu)return 4;
    owners[1].source_node_index=1;
    owners[1].source_node_name="boneroot";
    if(p3dOriginalTrackBind(&rig,owners,2,resolved)||
       resolved[0]!=0xffffu||resolved[1]!=0xffffu)return 5;
    owners[1].source_node_name="BoneRoot";
    owners[1].source_node_index=999;
    if(p3dOriginalTrackBind(&rig,owners,2,resolved)||
       resolved[0]!=0xffffu||resolved[1]!=0xffffu)return 6;
    owners[1].source_node_index=1;
    owners[1].source_node_name=NULL;
    if(p3dOriginalTrackBind(&rig,owners,2,resolved)||
       resolved[0]!=0xffffu||resolved[1]!=0xffffu)return 7;
    p3dOriginalSkeletonClear(&rig);
    owners[1].source_node_name="BoneRoot";
    if(p3dOriginalTrackBind(&rig,owners,2,resolved)||
       resolved[0]!=0xffffu||resolved[1]!=0xffffu)return 8;
    return 0;
}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    int status=check(argv[1]);
    if(status){fprintf(stderr,"C151 original track binding failed at %d\n",status);return 1;}
    puts("C151 exact original owner-to-node binding: PASS");
    return 0;
}
