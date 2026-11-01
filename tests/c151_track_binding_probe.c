#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "source_track_bindings.h"
static P3DOriginalSkeleton rig;
static P3DSourceTrackBindings binding;
int main(int argc,char **argv){
    if(argc!=5){fprintf(stderr,"usage: %s P3SK P3TB MODEL EXPECT_OK\n",argv[0]);return 2;}
    unsigned model=(unsigned)strtoul(argv[3],NULL,10);
    int expected=atoi(argv[4]);
    if(!p3dOriginalSkeletonLoad(&rig,argv[1],model))return 3;
    int loaded=p3dSourceTrackBindingsLoad(&binding,&rig,argv[2],model);
    if(loaded!=expected){fprintf(stderr,"unexpected track binding load %d != %d\n",loaded,expected);return 1;}
    if(loaded){
        if(!binding.ready||binding.model_id!=model||binding.count!=1||
           binding.node[0]!=1||binding.source_first_track[0]!=3)return 4;
    }else if(binding.ready||binding.count||binding.model_id)return 5;
    /* A failed model switch must never retain a prior binding. */
    if(loaded && p3dSourceTrackBindingsLoad(&binding,&rig,argv[2],model+1))return 6;
    if(binding.ready||binding.count)return 7;
    puts("C151 original source track-owner binding: PASS");
    return 0;
}
