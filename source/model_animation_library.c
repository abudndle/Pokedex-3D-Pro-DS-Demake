#include "model_animation_library.h"
#include <stdio.h>
#include <string.h>

static int load_slot(P3DAnimationClip *clip,const char *directory,
                     int resource,int slot){
    char path[128];
    int n;
    if(!directory||!directory[0]||resource<0||resource>=738||
       slot< -1||slot>=P3D_ANIMATION_LIBRARY_MAX-1)return 0;
    if(slot<0)
        n=snprintf(path,sizeof(path),"%s/p%03d.p3an",directory,resource);
    else
        n=snprintf(path,sizeof(path),"%s/p%03d_a%02d.p3an",
                   directory,resource,slot);
    if(n<0||(unsigned)n>=sizeof(path))return 0;
    return p3dAnimationLoad(clip,path);
}
int p3dAnimationLibraryLoad(P3DAnimationLibrary *library,
                            P3DAnimationClip *clip,
                            const char *directory,int resource_index){
    if(!library||!clip)return 0;
    memset(library,0,sizeof(*library));
    clip->ready=0;
    if(!directory||!directory[0]||resource_index<0||resource_index>=738)
        return 0;
    library->resource_index=resource_index;
    for(int slot=-1;slot<P3D_ANIMATION_LIBRARY_MAX-1;slot++){
        if(load_slot(clip,directory,resource_index,slot))
            library->slots[library->count++]=slot;
    }
    if(!library->count)return 0;
    library->selected=0;
    if(!load_slot(clip,directory,resource_index,library->slots[0])){
        library->count=0;
        clip->ready=0;
        return 0;
    }
    library->ready=1;
    return 1;
}
int p3dAnimationLibraryStep(P3DAnimationLibrary *library,
                            P3DAnimationClip *clip,
                            const char *directory,int direction){
    unsigned next;
    if(!library||!clip||!library->ready||library->count<2||
       library->count>P3D_ANIMATION_LIBRARY_MAX||!direction)return 0;
    next=direction>0?(library->selected+1)%library->count:
         (library->selected+library->count-1)%library->count;
    if(!load_slot(clip,directory,library->resource_index,
                  library->slots[next])){
        library->ready=0;
        clip->ready=0;
        return 0;
    }
    library->selected=next;
    return 1;
}
