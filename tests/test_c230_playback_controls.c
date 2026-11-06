#include "animation_playback.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
int main(void){
 P3DAnimationPlayback state={0};
 P3DAnimationClip clip={0};
 clip.ready=1;clip.version=2;clip.count=2;clip.total_ticks=5;
 /* Zero-based libnds H12 places the visible control glyphs at y96..103. */
 p3dPlaybackAdvance(&state,&clip,1);assert(state.tick==1);
 assert(p3dPlaybackTouch(&state,&clip,1,1,0,96));assert(state.paused);
 p3dPlaybackAdvance(&state,&clip,1);assert(state.tick==1);
 assert(p3dPlaybackTouch(&state,&clip,1,1,255,103));assert(state.tick==0&&state.paused);
 assert(p3dPlaybackTouch(&state,&clip,1,1,127,103));assert(!state.paused);
 for(int i=0;i<5;i++)p3dPlaybackAdvance(&state,&clip,1);
 assert(state.tick==0);
 state.tick=UINT_MAX;p3dPlaybackAdvance(&state,&clip,1);
 assert(state.tick==(UINT_MAX%5u+1)%5u);
 assert(p3dPlaybackTouch(&state,&clip,1,1,128,96));assert(!state.tick&&!state.paused);
 assert(!p3dPlaybackTouch(&state,&clip,1,1,-1,96));
 assert(!p3dPlaybackTouch(&state,&clip,1,1,256,96));
 assert(!p3dPlaybackTouch(&state,&clip,1,1,128,88));
 assert(!p3dPlaybackTouch(&state,&clip,1,1,128,95));
 assert(!p3dPlaybackTouch(&state,&clip,1,1,128,104));
 assert(!p3dPlaybackTouch(&state,&clip,1,0,0,96)); /* original bitmap art */
 assert(!p3dPlaybackTouch(&state,&clip,0,1,0,96)); /* static source geometry */
 state.tick=3;
 p3dPlaybackAdvance(&state,&clip,0);assert(state.tick==3);
 assert(!state.paused);
 clip.ready=0;
 assert(!p3dPlaybackTouch(&state,&clip,1,1,0,96));
 p3dPlaybackAdvance(&state,&clip,1);assert(state.tick==3);
 clip.ready=1;clip.total_ticks=0;
 assert(!p3dPlaybackTouch(&state,&clip,1,1,0,96));
 clip.total_ticks=5;clip.version=99;
 assert(!p3dPlaybackTouch(&state,&clip,1,1,0,96));
 clip.version=1;clip.count=P3D_ANIMATION_MAX_FRAMES+1;
 assert(!p3dPlaybackTouch(&state,&clip,1,1,0,96));
 clip.count=2;
 state.paused=1;state.tick=4;
 p3dPlaybackReset(&state);assert(!state.paused&&!state.tick);
 p3dPlaybackReset(NULL);p3dPlaybackAdvance(NULL,&clip,1);
 assert(!p3dPlaybackTouch(NULL,&clip,1,1,0,96));
 assert(!p3dPlaybackTouch(&state,NULL,1,1,0,96));
 puts("C230 animation pause/resume/restart, disabled render gates and tick wrap: PASS");
 return 0;
}
