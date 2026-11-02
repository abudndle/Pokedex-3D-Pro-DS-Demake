#ifndef P3D_ANIMATION_PLAYBACK_H
#define P3D_ANIMATION_PLAYBACK_H
#include "model_animation.h"
/* Inspection controls for a validated optional P3AN transform clip only.
 * Not source-verified 3DS skeletal playback; never animate P3VX/P3IX meshes. */
typedef struct { unsigned tick; int paused; } P3DAnimationPlayback;
void p3dPlaybackReset(P3DAnimationPlayback *playback);
void p3dPlaybackAdvance(P3DAnimationPlayback *playback,
                        const P3DAnimationClip *clip,int draws_clip);
/* Text-mode Pokédex row 12 (y=88..95): left pause/resume, right restart.
 * A hidden original-art UI or an undrawable clip MUST NOT accept controls.
 * Restart preserves the paused/playing state. 1 means action accepted. */
int p3dPlaybackTouch(P3DAnimationPlayback *playback,
                     const P3DAnimationClip *clip,int draws_clip,
                     int text_controls_visible,int x,int y);
#endif
