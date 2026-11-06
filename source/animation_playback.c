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
int p3dPlaybackTouch(P3DAnimationPlayback *playback,
                     const P3DAnimationClip *clip,int draws_clip,
                     int text_controls_visible,int x,int y){
    if(!playback||!text_controls_visible||!available(clip,draws_clip)||
       x<0||x>=256||y<P3D_PLAYBACK_CONTROL_ROW*8||y>=(P3D_PLAYBACK_CONTROL_ROW+1)*8)return 0;
    if(x<128)playback->paused=!playback->paused;
    else playback->tick=0;
    return 1;
}
