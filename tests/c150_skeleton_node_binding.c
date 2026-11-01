/* C150: host-compiled exact native P3SK node binding, synthetic data only. */
#include <stdio.h>
#include <string.h>
#include "original_skeleton.h"
static P3DOriginalSkeleton rig;
static int valid(const char *path){
    if(!p3dOriginalSkeletonLoad(&rig,path,14))return 1;
    if(p3dOriginalSkeletonFindNode(&rig,"Base")!=0 ||
       p3dOriginalSkeletonFindNode(&rig,"BoneRoot")!=1 ||
       p3dOriginalSkeletonFindNode(&rig,"boneroot")!=-1 ||
       p3dOriginalSkeletonFindNode(&rig,"")!=-1 ||
       p3dOriginalSkeletonFindNode(&rig,NULL)!=-1 ||
       p3dOriginalSkeletonFindNode(NULL,"Base")!=-1)return 2;
    char too_long[99];memset(too_long,'A',sizeof(too_long));too_long[98]=0;
    if(p3dOriginalSkeletonFindNode(&rig,too_long)!=-1)return 3;
    if(!p3dOriginalSkeletonIsAncestor(&rig,0,1) ||
       p3dOriginalSkeletonIsAncestor(&rig,1,0) ||
       p3dOriginalSkeletonIsAncestor(&rig,0,0) ||
       p3dOriginalSkeletonIsAncestor(&rig,0,999) ||
       p3dOriginalSkeletonIsAncestor(NULL,0,1))return 4;
    /* Fail closed even if a caller corrupts an already validated rig. */
    rig.records[56+48]=1;rig.records[56+49]=0;
    if(p3dOriginalSkeletonIsAncestor(&rig,0,1))return 5;
    p3dOriginalSkeletonClear(&rig);
    if(p3dOriginalSkeletonFindNode(&rig,"Base")!=-1 ||
       p3dOriginalSkeletonIsAncestor(&rig,0,1))return 6;
    return 0;
}
int main(int argc,char **argv){
    if(argc!=3){fprintf(stderr,"usage: %s P3SK EXPECT_VALID\n",argv[0]);return 2;}
    int expected=argv[2][0]=='1';
    int result=valid(argv[1]);
    if((result==0)!=expected){
        fprintf(stderr,"C150 native skeleton lookup mismatch expected=%d result=%d\n",expected,result);
        return 1;
    }
    if(!expected && (rig.ready||p3dOriginalSkeletonFindNode(&rig,"Base")!=-1))return 1;
    puts("C150 original-source node binding and ancestry: PASS");
    return 0;
}
