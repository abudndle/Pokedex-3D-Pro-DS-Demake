#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "source_track_bindings.h"
static P3DOriginalSkeleton rig;
static P3DSourceTrackBindings binding;
static void poison_binding(void){
    binding.model_id=0xffffu;binding.count=0xffffu;binding.ready=1;
    for(unsigned i=0;i<P3D_SKELETON_MAX_NODES;i++){
        binding.node[i]=0xffffu;
        binding.source_first_track[i]=0xffffffffu;
    }
}
static int binding_is_clear(void){
    if(binding.model_id||binding.count||binding.ready)return 0;
    for(unsigned i=0;i<P3D_SKELETON_MAX_NODES;i++)
        if(binding.node[i]||binding.source_first_track[i])return 0;
    return 1;
}
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
    /* A failed file open after success must clear every prior binding. */
    if(loaded){
        char missing[1024];
        int n=snprintf(missing,sizeof(missing),"%s.missing",argv[2]);
        if(n<0||(unsigned)n>=sizeof(missing))return 6;
        poison_binding();
        if(p3dSourceTrackBindingsLoad(&binding,&rig,missing,model))return 7;
        if(!binding_is_clear())return 8;
        /* Reload, poison the full capacity, then fail a model switch. */
        if(!p3dSourceTrackBindingsLoad(&binding,&rig,argv[2],model))return 9;
        poison_binding();
        if(p3dSourceTrackBindingsLoad(&binding,&rig,argv[2],model+1))return 10;
        if(!binding_is_clear())return 11;
        if(p3dSourceTrackBindingsLoad(NULL,&rig,argv[2],model))return 12;
    }
    puts("C151 original source track-owner binding: PASS");
    return 0;
}
