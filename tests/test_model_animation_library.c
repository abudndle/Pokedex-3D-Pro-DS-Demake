#include "model_animation_library.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DAnimationLibrary library={0};
 P3DAnimationClip clip={0};
 char corrupt_path[160];
 assert(argc==2);
 assert(p3dAnimationLibraryLoad(&library,&clip,argv[1],5));
 assert(library.ready && library.count==3 && library.selected==0);
 assert(library.slots[0]==-1 && library.slots[1]==0 && library.slots[2]==2);
 assert(clip.ready && clip.version==1 && clip.frames[0].yaw==1);
 assert(p3dAnimationLibraryStep(&library,&clip,argv[1],1));
 assert(library.selected==1 && clip.version==2 && clip.frames[0].yaw==20);
 assert(p3dAnimationLibraryStep(&library,&clip,argv[1],1));
 assert(library.selected==2 && clip.frames[0].yaw==40);
 assert(p3dAnimationLibraryStep(&library,&clip,argv[1],1));
 assert(library.selected==0 && clip.frames[0].yaw==1);
 assert(p3dAnimationLibraryStep(&library,&clip,argv[1],-1));
 assert(library.selected==2 && clip.frames[0].yaw==40);
 assert(!p3dAnimationLibraryStep(&library,&clip,argv[1],0));
 assert(library.selected==2 && clip.ready);
 assert(p3dAnimationLibraryLoad(&library,&clip,argv[1],6));
 assert(library.count==1 && library.slots[0]==0 && clip.ready);
 assert(!p3dAnimationLibraryStep(&library,&clip,argv[1],1));
 assert(library.count==1 && library.ready);
 assert(!p3dAnimationLibraryLoad(&library,&clip,argv[1],7));
 assert(!library.ready && library.count==0 && !clip.ready);
 assert(!p3dAnimationLibraryLoad(&library,&clip,argv[1],738));
 assert(!p3dAnimationLibraryLoad(&library,&clip,argv[1],-1));
 assert(!p3dAnimationLibraryLoad(&library,&clip,"",5));
 assert(!p3dAnimationLibraryLoad(NULL,&clip,argv[1],5));
 assert(!p3dAnimationLibraryLoad(&library,NULL,argv[1],5));
 assert(p3dAnimationLibraryLoad(&library,&clip,argv[1],5));
 assert(snprintf(corrupt_path,sizeof(corrupt_path),
                 "%s/p005_a00.p3an",argv[1])>0);
 assert(remove(corrupt_path)==0);
 assert(!p3dAnimationLibraryStep(&library,&clip,argv[1],1));
 assert(!library.ready && !clip.ready);
 puts("Verified multi-clip animation selection: PASS");
 return 0;
}
