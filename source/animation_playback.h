#ifndef P3D_ANIMATION_PLAYBACK_H
#define P3D_ANIMATION_PLAYBACK_H
#include "model_animation.h"
typedef struct { unsigned tick; int paused; } P3DAnimationPlayback;
void p3dPlaybackReset(P3DAnimationPlayback *playback);
void p3dPlaybackAdvance(P3DAnimationPlayback *playback,const P3DAnimationClip *clip);
/* Text-mode row 11: left half pauses/resumes, right half restarts.
 * Returns 1 only when a valid clip accepts the touch. Restart retains pause. */
int p3dPlaybackTouch(P3DAnimationPlayback *playback,const P3DAnimationClip *clip,int x,int y);
#endif
