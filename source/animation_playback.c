#include "animation_playback.h"
static int available(const P3DAnimationClip *clip){
    return clip && clip->ready && clip->count &&
           clip->count<=P3D_ANIMATION_MAX_FRAMES && clip->total_ticks;
}
void p3dPlaybackReset(P3DAnimationPlayback *playback){
    if(playback){playback->tick=0;playback->paused=0;}
}
void p3dPlaybackAdvance(P3DAnimationPlayback *playback,const P3DAnimationClip *clip){
    if(!playback || !available(clip) || playback->paused)return;
    playback->tick=(playback->tick%clip->total_ticks+1)%clip->total_ticks;
}
int p3dPlaybackTouch(P3DAnimationPlayback *playback,const P3DAnimationClip *clip,int x,int y){
    if(!playback || !available(clip) || x<0 || x>=256 || y<80 || y>=96)return 0;
    if(x<128)playback->paused=!playback->paused;
    else playback->tick=0;
    return 1;
}
