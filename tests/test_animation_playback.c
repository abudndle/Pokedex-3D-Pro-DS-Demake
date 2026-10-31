#include "animation_playback.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 P3DAnimationPlayback p={0};
 P3DAnimationClip clip={.count=2,.total_ticks=4,.ready=1};
 p3dPlaybackAdvance(&p,&clip); assert(p.tick==1);
 assert(p3dPlaybackTouch(&p,&clip,0,80)); assert(p.paused);
 p3dPlaybackAdvance(&p,&clip); assert(p.tick==1);
 assert(p3dPlaybackTouch(&p,&clip,255,95)); assert(p.tick==0 && p.paused);
 assert(p3dPlaybackTouch(&p,&clip,127,95)); assert(!p.paused);
 for(int i=0;i<4;i++)p3dPlaybackAdvance(&p,&clip);
 assert(p.tick==0);
 p.tick=3; assert(p3dPlaybackTouch(&p,&clip,128,80)); assert(p.tick==0);
 assert(!p3dPlaybackTouch(&p,&clip,-1,80));
 assert(!p3dPlaybackTouch(&p,&clip,256,80));
 assert(!p3dPlaybackTouch(&p,&clip,0,79));
 assert(!p3dPlaybackTouch(&p,&clip,0,96));
 clip.ready=0; assert(!p3dPlaybackTouch(&p,&clip,0,80));
 p3dPlaybackAdvance(&p,&clip); assert(p.tick==0);
 clip.ready=1; clip.total_ticks=0; p3dPlaybackAdvance(&p,&clip);
 assert(!p3dPlaybackTouch(&p,&clip,0,80));
 p.paused=1; p.tick=3; p3dPlaybackReset(&p); assert(!p.paused && !p.tick);
 p3dPlaybackReset(NULL); p3dPlaybackAdvance(NULL,&clip);
 assert(!p3dPlaybackTouch(NULL,&clip,0,80));
 puts("Animation pause, resume, restart and touch bounds: PASS");
}
