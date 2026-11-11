#include "animation_playback.h"
static int available(const P3DAnimationClip *clip,int draws_clip){
    return draws_clip && clip && clip->ready && clip->count &&
           clip->count<=P3D_ANIMATION_MAX_FRAMES &&
           (clip->version==1 || clip->version==2) && clip->total_ticks;
}
void p3dPlaybackReset(P3DAnimationPlayback *playback){
    if(playback){playback->tick=0;playback->paused=0;}
}
void p3dPlaybackAdvance(P3DAnimationPlayback *playback,
                        const P3DAnimationClip *clip,int draws_clip){
    unsigned next;
    if(!playback||playback->paused||!available(clip,draws_clip))return;
    next=playback->tick%clip->total_ticks;
    playback->tick=next+1u==clip->total_ticks?0u:next+1u;
}
